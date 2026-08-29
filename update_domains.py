import re
from pathlib import Path

app_py_path = "/root/server_panel/app.py"
with open(app_py_path, "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the entire # --- DOMAINS AND SSL --- block
start_marker = "# --- DOMAINS AND SSL ---"
end_marker = "# --- PHP CGI PROXY FOR WEBHOOKS ---"

if start_marker in content and end_marker in content:
    pre = content.split(start_marker)[0]
    post = content.split(end_marker)[1]
    
    new_domains_code = """
# --- DOMAINS AND SSL ---
class DomainCreateRequest(BaseModel):
    domain: str
    type: str
    document_root: Optional[str] = None
    proxy_url: Optional[str] = None
    force_https: Optional[bool] = False

class DomainActionRequest(BaseModel):
    domain: str

@app.get("/api/domains/list")
async def get_domains_list(sess: dict = Depends(verify_session)):
    try:
        domains = []
        nginx_dir = Path("/etc/nginx/sites-enabled")
        if not nginx_dir.exists():
            return JSONResponse({"success": True, "domains": []})
        
        for conf_file in nginx_dir.glob("*"):
            if conf_file.is_file() and conf_file.name != "default":
                content = conf_file.read_text()
                is_proxy = "proxy_pass" in content
                
                doc_root_match = re.search(r"root\s+([^;]+);", content)
                doc_root = doc_root_match.group(1) if doc_root_match else None
                
                proxy_match = re.search(r"proxy_pass\s+([^;]+);", content)
                proxy_url = proxy_match.group(1) if proxy_match else None
                
                has_ssl = "ssl_certificate" in content
                force_https = "return 301 https://$host$request_uri;" in content or "return 301 https://$server_name$request_uri;" in content
                
                ssl_expiry = None
                ssl_issuer = None
                
                if has_ssl:
                    import subprocess, datetime
                    cert_path_match = re.search(r"ssl_certificate\s+([^;]+);", content)
                    if cert_path_match:
                        cert_path = cert_path_match.group(1).strip()
                        if Path(cert_path).exists():
                            try:
                                out = subprocess.check_output(["openssl", "x509", "-enddate", "-issuer", "-noout", "-in", cert_path], text=True)
                                for line in out.splitlines():
                                    if line.startswith("notAfter="):
                                        date_str = line.split("=")[1].strip()
                                        dt = datetime.datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
                                        ssl_expiry = dt.strftime("%Y-%m-%d")
                                    elif line.startswith("issuer="):
                                        ssl_issuer = "Let's Encrypt" if "Let's Encrypt" in line or "O =" not in line else line.split("O =")[-1].split(",")[0].strip()
                            except:
                                pass
                
                domains.append({
                    "domain": conf_file.name,
                    "type": "proxy" if is_proxy else "static",
                    "root": doc_root,
                    "proxy_url": proxy_url,
                    "ssl": has_ssl,
                    "ssl_expiry": ssl_expiry,
                    "ssl_issuer": ssl_issuer,
                    "force_https": force_https
                })
        return JSONResponse({"success": True, "domains": domains})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

def generate_nginx_conf(req: DomainCreateRequest, existing_ssl_lines=None):
    conf_lines = []
    
    # HTTP Server Block
    conf_lines.append("server {")
    conf_lines.append("    listen 80;")
    conf_lines.append(f"    server_name {req.domain} www.{req.domain};")
    
    if req.force_https and existing_ssl_lines:
        conf_lines.append("    return 301 https://$host$request_uri;")
        conf_lines.append("}")
        conf_lines.append("")
        conf_lines.append("server {")
        conf_lines.append("    listen 443 ssl;")
        conf_lines.append(f"    server_name {req.domain} www.{req.domain};")
        conf_lines.extend(["    " + l.strip() for l in existing_ssl_lines])
    else:
        # If no SSL yet but force_https requested, we can't redirect yet or it breaks validation
        pass

    if req.type == "static":
        root = req.document_root or f"/var/www/{req.domain}"
        Path(root).mkdir(parents=True, exist_ok=True)
        conf_lines.append(f"    root {root};")
        conf_lines.append("    index index.html index.php;")
        conf_lines.append("    location / {")
        conf_lines.append("        try_files $uri $uri/ =404;")
        conf_lines.append("    }")
    else:
        proxy = req.proxy_url or "http://127.0.0.1:8080"
        conf_lines.append("    location / {")
        conf_lines.append(f"        proxy_pass {proxy};")
        conf_lines.append("        proxy_set_header Host $host;")
        conf_lines.append("        proxy_set_header X-Real-IP $remote_addr;")
        conf_lines.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
        conf_lines.append("        proxy_set_header X-Forwarded-Proto $scheme;")
        conf_lines.append("    }")
        
    if not req.force_https and existing_ssl_lines:
        # If they don't want force HTTPS but have SSL, we need to make sure SSL block is there
        # Certbot usually modifies the file directly, so this is a basic fallback
        conf_lines.extend(["    " + l.strip() for l in existing_ssl_lines])
        
    conf_lines.append("}")
    return "\\n".join(conf_lines)

@app.post("/api/domains/create")
async def create_domain_config(req: DomainCreateRequest, sess: dict = Depends(verify_session)):
    if not re.match(r"^[a-zA-Z0-9.-]+$", req.domain):
        return JSONResponse({"success": False, "error": "اسم النطاق غير صالح"})
        
    avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
    enabled_path = Path(f"/etc/nginx/sites-enabled/{req.domain}")
    
    conf = generate_nginx_conf(req)
    try:
        avail_path.write_text(conf)
        if not enabled_path.exists():
            enabled_path.symlink_to(avail_path)
            
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        return JSONResponse({"success": True, "message": f"تمت إضافة النطاق {req.domain} بنجاح."})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/domains/edit")
async def edit_domain_config(req: DomainCreateRequest, sess: dict = Depends(verify_session)):
    if not re.match(r"^[a-zA-Z0-9.-]+$", req.domain):
        return JSONResponse({"success": False, "error": "اسم النطاق غير صالح"})
        
    avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
    enabled_path = Path(f"/etc/nginx/sites-enabled/{req.domain}")
    
    existing_ssl_lines = []
    if avail_path.exists():
        existing_conf = avail_path.read_text()
        existing_ssl_lines = [line for line in existing_conf.split("\\n") if "ssl_certificate" in line or "ssl_dhparam" in line or "managed by Certbot" in line or "listen 443" in line]
    
    conf = generate_nginx_conf(req, existing_ssl_lines)

    try:
        avail_path.write_text(conf)
        if not enabled_path.exists():
            enabled_path.symlink_to(avail_path)
            
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        return JSONResponse({"success": True, "message": f"تم تعديل النطاق {req.domain} بنجاح."})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/domains/delete")
async def delete_domain_config(req: DomainActionRequest, sess: dict = Depends(verify_session)):
    avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
    enabled_path = Path(f"/etc/nginx/sites-enabled/{req.domain}")
    try:
        if enabled_path.exists():
            enabled_path.unlink()
        if avail_path.exists():
            avail_path.unlink()
            
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        subprocess.run(["certbot", "delete", "--cert-name", req.domain, "--non-interactive"])
        return JSONResponse({"success": True, "message": f"تم حذف النطاق {req.domain} بجميع بياناته."})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/domains/ssl")
async def request_domain_ssl(req: DomainActionRequest, sess: dict = Depends(verify_session)):
    try:
        # Check if force_https is currently on, so we apply --redirect
        avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
        cmd = ["certbot", "--nginx", "-d", req.domain, "--non-interactive", "--agree-tos", "--register-unsafely-without-email"]
        
        if avail_path.exists() and "return 301 https" in avail_path.read_text():
            cmd.append("--redirect")
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return JSONResponse({"success": True, "message": "تم إصدار/تجديد شهادة SSL بنجاح!"})
        else:
            err = result.stderr or result.stdout
            return JSONResponse({"success": False, "error": f"فشل تثبيت SSL: {err}"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

"""
    
    new_file = pre + start_marker + "\n" + new_domains_code.strip() + "\n\n" + end_marker + post
    with open(app_py_path, "w", encoding="utf-8") as f:
        f.write(new_file)
    print("Backend updated.")
else:
    print("Markers not found.")
