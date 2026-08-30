import os
import sys
import pty
import fcntl
import termios
import struct
import asyncio
import hashlib
import secrets
import shutil
import time
import platform
import subprocess
import json
import logging
import re
import pyotp
import qrcode
import io
import base64
from typing import Optional, List
from pathlib import Path
import psutil
import re
import collections
import sqlite3
import tarfile
import urllib.request
import urllib.parse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header, Cookie, Response, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- CONFIG & AUTH ---
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

import json

SESSION_FILE = BASE_DIR / "sessions.json"
SESSION_STORE = {}

def load_sessions():
    global SESSION_STORE
    if SESSION_FILE.exists():
        try:
            with open(SESSION_FILE, "r") as f:
                SESSION_STORE = json.load(f)
        except:
            SESSION_STORE = {}
    else:
        SESSION_STORE = {}

def save_sessions():
    tmp = SESSION_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(SESSION_STORE, f)
    os.replace(tmp, SESSION_FILE)

load_sessions()


# Default Credentials: username: admin / password: admin_password_123
# (User can easily change password from UI or config)
DEFAULT_USER = "admin"
DEFAULT_PASS = "admin123456"

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class ConfigManager:
    @staticmethod
    def load():
        if CONFIG_FILE.exists():
            import json
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Default config
        cfg = {
            "username": DEFAULT_USER,
            "password_hash": get_password_hash(DEFAULT_PASS),
            "port": 8090,
            "root_path": "/"
        }
        ConfigManager.save(cfg)
        return cfg

    @staticmethod
    def save(cfg):
        import json
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

config = ConfigManager.load()

app = FastAPI(title="curlHUB")

# --- SECURITY SHIELD & ATTACK DEFENSE MANAGER ---
KNOWN_SCANNER_AGENTS = [
    "sqlmap", "nikto", "gobuster", "dirsearch", "wpscan", "nuclei",
    "nmap", "masscan", "acunetix", "nessus", "openvas", "ffuf",
    "dirbuster", "hydra", "medusa", "zgrab", "shodan", "censys", "netsparker"
]

HONEYPOT_PROBES = [
    "/.env", "/.git", "/wp-config", "/phpmyadmin", "/pma", "/admin.php",
    "/shell.php", "/xmlrpc.php", "/.aws", "/id_rsa", "/wp-login.php",
    "/config.json", "/web.config", "/.svn", "/backup.zip", "/dump.sql",
    "/etc/passwd", "/win.ini", "/cgi-bin", "/.htaccess", "/eval-stdin.php"
]

class SecurityShieldManager:
    def __init__(self):
        self.events = collections.deque(maxlen=1000)
        self.banned_ips = {}
        self.fuzz_tracker = {}
        self.stats = {
            "total_blocked": 0,
            "brute_force_blocked": 0,
            "scanners_blocked": 0,
            "honeypot_trapped": 0,
            "injection_blocked": 0
        }

    def is_banned(self, ip: str) -> tuple:
        now = time.time()
        if ip in self.banned_ips:
            info = self.banned_ips[ip]
            if info["expires_at"] > now:
                remaining = int(info["expires_at"] - now)
                return True, info["reason"], remaining
            else:
                del self.banned_ips[ip]
        return False, "", 0

    def ban_ip(self, ip: str, reason: str, duration: int = 1800):
        now = time.time()
        self.banned_ips[ip] = {
            "ip": ip,
            "reason": reason,
            "banned_at": now,
            "expires_at": now + duration,
            "duration_minutes": int(duration / 60)
        }
        self.stats["total_blocked"] += 1

    def unban_ip(self, ip: str) -> bool:
        if ip in self.banned_ips:
            del self.banned_ips[ip]
            return True
        return False

    def clear_logs(self):
        self.events.clear()

    def record_event(self, ip: str, threat_type: str, path: str, detail: str, user_agent: str, action: str = "BLOCKED", severity: str = "HIGH"):
        now = time.time()
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        event = {
            "id": len(self.events) + 1,
            "timestamp": now,
            "time_str": time_str,
            "ip": ip,
            "threat_type": threat_type,
            "path": path,
            "detail": detail,
            "user_agent": (user_agent or "Unknown")[:120],
            "action": action,
            "severity": severity
        }
        self.events.appendleft(event)
        self.stats["total_blocked"] += 1
        
        t_lower = threat_type.lower()
        if "تخمين" in threat_type or "login" in t_lower or "brute" in t_lower:
            self.stats["brute_force_blocked"] += 1
        elif "scanner" in t_lower or "fuzz" in t_lower or "فحص" in threat_type:
            self.stats["scanners_blocked"] += 1
        elif "honeypot" in t_lower or "فخ" in threat_type:
            self.stats["honeypot_trapped"] += 1
        elif "حقن" in threat_type or "injection" in t_lower:
            self.stats["injection_blocked"] += 1

    def record_fuzz_attempt(self, ip: str, path: str, user_agent: str, is_honeypot: bool = False):
        now = time.time()
        if ip not in self.fuzz_tracker:
            self.fuzz_tracker[ip] = {"count": 1, "first_seen": now}
        else:
            data = self.fuzz_tracker[ip]
            if now - data["first_seen"] > 60:
                self.fuzz_tracker[ip] = {"count": 1, "first_seen": now}
            else:
                data["count"] += 1

        count = self.fuzz_tracker[ip]["count"]
        
        if is_honeypot:
            self.record_event(
                ip=ip,
                threat_type="فخ مسارات حساسة (Honeypot Trap)",
                path=path,
                detail=f"محاولة استكشاف ملف/مسار محمي ومشبوه ({path})",
                user_agent=user_agent,
                action="TRAPPED",
                severity="CRITICAL"
            )
            if count >= 2:
                self.ban_ip(ip, f"تكرار فحص ملفات حساسة ومسارات محظورة ({path})", duration=3600)
        else:
            if count >= 15:
                self.ban_ip(ip, "تخمين وفحص مسارات مكثف ومشبوه (Path Fuzzing / Brute-Force)", duration=1800)
                self.record_event(
                    ip=ip,
                    threat_type="تخمين مسارات عشوائي (Directory Fuzzing / Brute-Force)",
                    path=path,
                    detail=f"تم رصد أكثر من 15 طلب فحص مسارات غير موجودة في دقيقة واحدة",
                    user_agent=user_agent,
                    action="BANNED (30m)",
                    severity="HIGH"
                )

SECURITY_SHIELD = SecurityShieldManager()

def get_client_ip(request: Request) -> str:
    client_host = request.client.host if request.client else "127.0.0.1"
    # Only trust proxy headers if the request comes from localhost
    if client_host in ("127.0.0.1", "::1"):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First IP in list is client's original IP
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return client_host

# Global Security Shield & Headers Middleware
@app.middleware("http")
async def security_shield_middleware(request: Request, call_next):
    client_ip = get_client_ip(request)
    path = request.url.path
    user_agent = request.headers.get("User-Agent", "").lower()
    
    # Check if request is from authenticated admin
    auth_header = request.headers.get("Authorization", "")
    is_authenticated_admin = False
    if auth_header.startswith("Bearer "):
        tok = auth_header.split(" ")[1]
        if tok in SESSION_STORE:
            is_authenticated_admin = True
            
    # 1. Check if IP is currently banned (Skip if authenticated admin managing panel)
    if not is_authenticated_admin and client_ip not in ["127.0.0.1", "::1"]:
        is_banned, ban_reason, remaining_secs = SECURITY_SHIELD.is_banned(client_ip)
        if is_banned:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "IP_BANNED",
                    "detail": f"تم حظر عنوانك مؤقتاً بسبب نشاط مشبوه ({ban_reason}). يرجى الانتظار {remaining_secs} ثانية."
                }
            )
        
    # 2. Check for Known Security Scanner User-Agents (e.g. gobuster, nikto, sqlmap, etc.)
    for scanner in KNOWN_SCANNER_AGENTS:
        if scanner in user_agent:
            if client_ip not in ["127.0.0.1", "::1"]:
                SECURITY_SHIELD.ban_ip(client_ip, f"استخدام أداة فحص واختراق أمنية مكشوفة ({scanner})", duration=3600)
            SECURITY_SHIELD.record_event(
                ip=client_ip,
                threat_type="أداة فحص واختراق أمني (Security Scanner)",
                path=path,
                detail=f"تم رصد واعتراض أداة الهجوم '{scanner}' في ترويسة الطلب",
                user_agent=user_agent,
                action="BANNED (1h)" if client_ip not in ["127.0.0.1", "::1"] else "BLOCKED",
                severity="CRITICAL"
            )
            return JSONResponse(
                status_code=403,
                content={"error": "SCANNER_BLOCKED", "detail": "تم اكتشاف أداة فحص أمنية غير مصرح بها وحظر الاتصال."}
            )

    # 3. Check for Honeypot Sensitive Traps (e.g. /.env, /phpmyadmin, /.git, etc.)
    path_lower = path.lower()
    for probe in HONEYPOT_PROBES:
        if probe in path_lower:
            SECURITY_SHIELD.record_fuzz_attempt(client_ip, path, user_agent, is_honeypot=True)
            return JSONResponse(status_code=404, content={"error": "Not Found"})

    response = await call_next(request)

    # 4. If status is 404 on probing
    if response.status_code == 404 and not path.startswith("/static/"):
        SECURITY_SHIELD.record_fuzz_attempt(client_ip, path, user_agent, is_honeypot=False)

    # 5. Inject Security Response Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*$", # Allow all but be compatible with credentials
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
def verify_session(request: Request, session_token: Optional[str] = Cookie(None)):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif session_token:
        token = session_token
    
    if not token or token not in SESSION_STORE:
        raise HTTPException(status_code=401, detail="غير مصرح به (Unauthorized)")
    
    # Check expiry (7 days)
    sess = SESSION_STORE[token]
    if time.time() - sess.get("created_at", 0) > 7 * 86400:
        del SESSION_STORE[token]
        raise HTTPException(status_code=401, detail="انتهت صلاحية الجلسة")
        
    return sess

class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False
    totp_code: Optional[str] = None

class ChangePassRequest(BaseModel):
    old_password: str
    new_password: str

class Enable2FARequest(BaseModel):
    totp_code: str
    secret: str

class Disable2FARequest(BaseModel):
    password: str

class FileSaveRequest(BaseModel):
    path: str
    content: str

class CreateItemRequest(BaseModel):
    parent_path: str
    name: str
    is_dir: bool

class RenameItemRequest(BaseModel):
    old_path: str
    new_path: str

class DeleteItemRequest(BaseModel):
    path: str

class ChmodRequest(BaseModel):
    path: str
    permissions: str

class CompressRequest(BaseModel):
    path: str

class KillProcessRequest(BaseModel):
    pid: int

class ServiceActionRequest(BaseModel):
    service: str
    action: str  # start, stop, restart, reload, status

class BanIpRequest(BaseModel):
    ip: str
    reason: Optional[str] = "حظر يدوي بواسطة المسؤول"
    duration_minutes: Optional[int] = 30

class UnbanIpRequest(BaseModel):
    ip: str

@app.post("/api/auth/login")
async def login(req: LoginRequest, request: Request, response: Response):
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    now = time.time()
    
    # Check if IP is banned
    is_banned, ban_reason, remaining_secs = SECURITY_SHIELD.is_banned(client_ip)
    if is_banned:
        raise HTTPException(
            status_code=429, 
            detail=f"تم حظر محاولات تسجيل الدخول مؤقتاً بسبب نشاط مشبوه ({ban_reason}). يرجى الانتظار {remaining_secs} ثانية."
        )

    cfg = ConfigManager.load()
    input_hash = get_password_hash(req.password)
    
    # Constant-time comparison to prevent timing attacks
    user_match = secrets.compare_digest(req.username, cfg["username"])
    pass_match = secrets.compare_digest(input_hash, cfg["password_hash"])
    
    if user_match and pass_match:
        if cfg.get("2fa_enabled") and cfg.get("2fa_secret"):
            if not req.totp_code:
                return {"status": "2fa_required"}
            totp = pyotp.TOTP(cfg.get("2fa_secret"))
            if not totp.verify(req.totp_code):
                if client_ip not in SECURITY_SHIELD.fuzz_tracker:
                    SECURITY_SHIELD.fuzz_tracker[client_ip] = {"count": 1, "first_seen": now}
                else:
                    SECURITY_SHIELD.fuzz_tracker[client_ip]["count"] += 1
                raise HTTPException(status_code=401, detail="رمز التحقق غير صحيح")

        SECURITY_SHIELD.fuzz_tracker.pop(client_ip, None)
        token = secrets.token_hex(32)
        SESSION_STORE[token] = {
            "username": req.username,
            "created_at": now
        }
        save_sessions()
        
        max_age = 7 * 86400 if req.remember else None
        
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=False,
            max_age=max_age,
            samesite="lax"
        )
        return {"status": "success", "token": token, "username": req.username}
        
    # Record failed login
    if client_ip not in SECURITY_SHIELD.fuzz_tracker:
        SECURITY_SHIELD.fuzz_tracker[client_ip] = {"count": 1, "first_seen": now}
    else:
        SECURITY_SHIELD.fuzz_tracker[client_ip]["count"] += 1
        
    failed_count = SECURITY_SHIELD.fuzz_tracker[client_ip]["count"]
    
    SECURITY_SHIELD.record_event(
        ip=client_ip,
        threat_type="تخمين كلمة المرور (Login Brute-Force)",
        path="/api/auth/login",
        detail=f"محاولة فاشلة لتسجيل الدخول للمستخدم '{req.username}' (المحاولة {failed_count}/5)",
        user_agent=user_agent,
        action="AUTH_FAILED",
        severity="MEDIUM" if failed_count < 3 else "HIGH"
    )
    
    if failed_count >= 5:
        # Lock out for 15 minutes (900 seconds)
        SECURITY_SHIELD.ban_ip(client_ip, "تكرار محاولات تسجيل الدخول الخاطئة (5 محاولات فاشلة)", duration=900)
        SECURITY_SHIELD.record_event(
            ip=client_ip,
            threat_type="تخمين كلمة المرور (Login Brute-Force)",
            path="/api/auth/login",
            detail="تجاوز الحد الأقصى للمحاولات الفاشلة - تم تطبيق الحظر التلقائي لمدة 15 دقيقة",
            user_agent=user_agent,
            action="BANNED (15m)",
            severity="CRITICAL"
        )
        raise HTTPException(
            status_code=429,
            detail="تم حظر تسجيل الدخول لمدة 15 دقيقة بسبب تكرار المحاولات الخاطئة (5 محاولات فاشلة)."
        )
        
    remaining_attempts = 5 - failed_count
    raise HTTPException(
        status_code=401, 
        detail=f"اسم المستخدم أو كلمة المرور غير صحيحة. المتبقي: {remaining_attempts} محاولات قبل الحظر المؤقت."
    )

@app.post("/api/auth/logout")
async def logout(response: Response, sess: dict = Depends(verify_session), session_token: Optional[str] = Cookie(None)):
    if session_token and session_token in SESSION_STORE:
        del SESSION_STORE[session_token]
    response.delete_cookie("session_token")
    return {"status": "success"}

# --- SECURITY MONITOR & SHIELD APIS ---
@app.get("/api/security/stats")
async def get_security_stats(sess: dict = Depends(verify_session)):
    now = time.time()
    active_bans = [
        {
            "ip": v["ip"],
            "reason": v["reason"],
            "banned_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(v["banned_at"])),
            "remaining_seconds": max(0, int(v["expires_at"] - now)),
            "remaining_minutes": max(0, int((v["expires_at"] - now) / 60))
        }
        for v in SECURITY_SHIELD.banned_ips.values() if v["expires_at"] > now
    ]
    
    return {
        "status": "success",
        "shield_active": True,
        "stats": SECURITY_SHIELD.stats,
        "banned_ips": active_bans,
        "banned_count": len(active_bans),
        "total_events_count": len(SECURITY_SHIELD.events)
    }

@app.get("/api/security/logs")
async def get_security_logs(limit: int = 150, sess: dict = Depends(verify_session)):
    logs = list(SECURITY_SHIELD.events)[:limit]
    return {
        "status": "success",
        "logs": logs
    }

@app.post("/api/security/ban")
async def ban_ip_endpoint(req: BanIpRequest, sess: dict = Depends(verify_session)):
    ip = req.ip.strip()
    if not ip or len(ip) > 45:
        raise HTTPException(status_code=400, detail="عنوان IP غير صالح")
    duration = (req.duration_minutes or 30) * 60
    SECURITY_SHIELD.ban_ip(ip, req.reason or "حظر يدوي بواسطة المسؤول", duration=duration)
    SECURITY_SHIELD.record_event(
        ip=ip,
        threat_type="حظر يدوي (Manual Ban)",
        path="*",
        detail=req.reason or "حظر يدوي من لوحة التحكم",
        user_agent="Admin Panel",
        action="BANNED",
        severity="MEDIUM"
    )
    return {"status": "success", "message": f"تم حظر العنوان {ip} بنجاح"}

@app.post("/api/security/unban")
async def unban_ip_endpoint(req: UnbanIpRequest, sess: dict = Depends(verify_session)):
    ip = req.ip.strip()
    removed = SECURITY_SHIELD.unban_ip(ip)
    if removed:
        return {"status": "success", "message": f"تم فك الحظر عن العنوان {ip} بنجاح"}
    return {"status": "not_found", "message": f"العنوان {ip} غير موجود في قائمة الحظر"}

@app.post("/api/security/logs/clear")
async def clear_security_logs(sess: dict = Depends(verify_session)):
    SECURITY_SHIELD.clear_logs()
    return {"status": "success", "message": "تم تفريغ سجلات الأمان بنجاح"}

@app.get("/api/auth/check")
async def check_auth(sess: dict = Depends(verify_session)):
    return {"status": "authenticated", "username": sess["username"]}

@app.post("/api/auth/change-password")
async def change_password(req: ChangePassRequest, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    if get_password_hash(req.old_password) != cfg["password_hash"]:
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="كلمة المرور يجب أن تكون 6 خانات على الأقل")
    
    cfg["password_hash"] = get_password_hash(req.new_password)
    ConfigManager.save(cfg)
    return {"status": "success", "message": "تم تحديث كلمة المرور بنجاح"}

@app.get("/api/auth/2fa/status")
async def get_2fa_status(sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    return {"enabled": cfg.get("2fa_enabled", False)}

@app.get("/api/auth/2fa/setup")
async def setup_2fa(sess: dict = Depends(verify_session)):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    cfg = ConfigManager.load()
    username = cfg.get("username", "admin")
    provisioning_uri = totp.provisioning_uri(name=username, issuer_name="ServerPanel")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    qr_base64 = f"data:image/png;base64,{img_str}"
    
    return {"secret": secret, "qr_code": qr_base64}

@app.post("/api/auth/2fa/enable")
async def enable_2fa(req: Enable2FARequest, sess: dict = Depends(verify_session)):
    totp = pyotp.TOTP(req.secret)
    if not totp.verify(req.totp_code):
        raise HTTPException(status_code=400, detail="الرمز غير صحيح، حاول مرة أخرى")
        
    cfg = ConfigManager.load()
    cfg["2fa_secret"] = req.secret
    cfg["2fa_enabled"] = True
    ConfigManager.save(cfg)
    return {"status": "success", "message": "تم تفعيل المصادقة الثنائية بنجاح"}

@app.post("/api/auth/2fa/disable")
async def disable_2fa(req: Disable2FARequest, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    if get_password_hash(req.password) != cfg["password_hash"]:
        raise HTTPException(status_code=400, detail="كلمة المرور غير صحيحة")
        
    cfg["2fa_secret"] = ""
    cfg["2fa_enabled"] = False
    ConfigManager.save(cfg)
    return {"status": "success", "message": "تم تعطيل المصادقة الثنائية بنجاح"}

# --- SYSTEM STATS & COMPREHENSIVE MONITOR API ---
@app.get("/api/system/stats")
async def get_system_stats(sess: dict = Depends(verify_session)):
    cpu_percent = await asyncio.to_thread(psutil.cpu_percent, 0.1)
    cpu_count = psutil.cpu_count()
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')
    
    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "load_1": round(load_avg[0], 2),
            "load_5": round(load_avg[1], 2),
            "load_15": round(load_avg[2], 2)
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        },
        "swap": {
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
            "free_gb": round(swap.free / (1024**3), 2),
            "percent": swap.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        "uptime_seconds": int(uptime_seconds)
    }

@app.get("/api/system/monitor")
async def get_full_system_monitor(sess: dict = Depends(verify_session)):
    load_avg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    cpu_percent = await asyncio.to_thread(psutil.cpu_percent, 0.1)
    cpu_cores = psutil.cpu_count(logical=True) or 1
    cpu_physical = psutil.cpu_count(logical=False) or cpu_cores
    per_cpu = psutil.cpu_percent(interval=None, percpu=True)
    
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # Storage Partitions
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent
            })
        except Exception:
            pass
            
    # Network I/O
    net_io = psutil.net_io_counters()
    
    # Accurate Real-Time Processes via ps
    proc_summary = {"total": 0, "running": 0, "sleeping": 0, "stopped": 0, "zombie": 0}
    processes = []
    
    try:
        cmd_ps = ['ps', '-eo', 'pid,user,%cpu,%mem,rss,stat,comm,args', '--sort=-%cpu']
        out_ps = await asyncio.to_thread(subprocess.check_output, cmd_ps, text=True)
        lines = out_ps.strip().split('\n')
        for line in lines[1:]:
            parts = line.split(None, 7)
            if len(parts) >= 8:
                pid_str, user, cpu_str, mem_pct_str, rss_str, stat_code, comm, args = parts
                proc_summary["total"] += 1
                
                # Determine state
                st_label = "sleeping"
                if "R" in stat_code:
                    st_label = "running"
                    proc_summary["running"] += 1
                elif "Z" in stat_code:
                    st_label = "zombie"
                    proc_summary["zombie"] += 1
                elif "T" in stat_code:
                    st_label = "stopped"
                    proc_summary["stopped"] += 1
                else:
                    proc_summary["sleeping"] += 1
                    
                try:
                    cpu_val = float(cpu_str)
                    mem_pct_val = float(mem_pct_str)
                    mem_mb_val = round(int(rss_str) / 1024, 1)
                    pid_val = int(pid_str)
                except ValueError:
                    continue
                    
                # Clean command line
                cmd_clean = args.strip() if args else comm
                
                processes.append({
                    "pid": pid_val,
                    "name": comm,
                    "user": user,
                    "cpu_percent": cpu_val,
                    "memory_percent": mem_pct_val,
                    "memory_mb": mem_mb_val,
                    "status": st_label,
                    "stat_code": stat_code,
                    "threads": 1,
                    "cmdline": cmd_clean[:180]
                })
    except Exception as e:
        pass
        
    # Sort top processes by CPU % descending, then RAM MB
    processes.sort(key=lambda x: (x["cpu_percent"], x["memory_mb"]), reverse=True)
    
    # System Services (Systemd)
    services = []
    try:
        cmd_srv = ['systemctl', 'list-units', '--type=service', '--state=running,failed,active', '--no-legend', '--no-pager']
        out_srv = await asyncio.to_thread(subprocess.check_output, cmd_srv, text=True)
        for line in out_srv.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                unit = parts[0]
                active = parts[2]
                sub = parts[3]
                desc = ' '.join(parts[4:])
                
                # Ignore systemd auto slices / scopes
                if unit.endswith('.service') and not unit.startswith('systemd-'):
                    srv_name = unit.replace('.service', '')
                    services.append({
                        "unit": unit,
                        "name": srv_name,
                        "status": active,
                        "sub_status": sub,
                        "desc": desc
                    })
    except Exception:
        pass

    # Listening Ports
    ports = []
    seen = set()
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' or conn.type == 2: # SOCK_DGRAM
                key = (conn.laddr.port, conn.type, conn.laddr.ip)
                if key in seen:
                    continue
                seen.add(key)
                
                p_name = "Unknown"
                if conn.pid:
                    try:
                        p_name = psutil.Process(conn.pid).name()
                    except Exception:
                        pass
                proto = "TCP" if conn.type == 1 else "UDP"
                ports.append({
                    "port": conn.laddr.port,
                    "ip": conn.laddr.ip,
                    "proto": proto,
                    "status": conn.status or "Active",
                    "pid": conn.pid or 0,
                    "process_name": p_name
                })
    except Exception:
        pass
        
    ports.sort(key=lambda x: (x["port"], x["proto"]))
    
    # Uptime format
    boot_time = psutil.boot_time()
    uptime_sec = int(time.time() - boot_time)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    minutes = (uptime_sec % 3600) // 60
    uptime_str = f"{days} يوم {hours} ساعة {minutes} دقيقة" if days > 0 else f"{hours} ساعة {minutes} دقيقة"
    
    return {
        "system": {
            "hostname": platform.node(),
            "os": f"{platform.system()} {platform.release()}",
            "uptime_seconds": uptime_sec,
            "uptime_str": uptime_str,
            "load_1": round(load_avg[0], 2),
            "load_5": round(load_avg[1], 2),
            "load_15": round(load_avg[2], 2)
        },
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_cores,
            "physical_cores": cpu_physical,
            "per_cpu": per_cpu
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "free_gb": round(mem.free / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "cached_mb": round(getattr(mem, "cached", 0) / (1024**2), 1),
            "buffers_mb": round(getattr(mem, "buffers", 0) / (1024**2), 1),
            "percent": mem.percent
        },
        "swap": {
            "total_gb": round(swap.total / (1024**3), 2),
            "used_gb": round(swap.used / (1024**3), 2),
            "free_gb": round(swap.free / (1024**3), 2),
            "percent": swap.percent
        },
        "disk": {
            "partitions": partitions
        },
        "network": {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 1),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 1)
        },
        "proc_summary": proc_summary,
        "processes": processes[:60],
        "services": services,
        "ports": ports
    }

@app.post("/api/system/service/action")
async def service_action(req: ServiceActionRequest, sess: dict = Depends(verify_session)):
    valid_actions = ["restart", "stop", "start", "reload", "status"]
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail="إجراء غير مدعوم")
        
    srv = req.service.strip()
    if not re.match(r'^[a-zA-Z0-9_\-\.@]+$', srv) or len(srv) > 100:
        raise HTTPException(status_code=400, detail="اسم الخدمة غير صالح ويحتوي على رموز غير مسموحة")

    if not srv.endswith('.service') and '.' not in srv:
        srv = f"{srv}.service"
        
    # Prevent stopping crucial panel service directly without warning
    if srv == "server-panel.service" and req.action == "stop":
        raise HTTPException(status_code=400, detail="محمي: إيقاف لوحة التحكم سيؤدي لقطع الاتصال بك!")
        
    try:
        cmd = ["systemctl", req.action, srv]
        res = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            act_names = {"restart": "إعادة تشغيل", "stop": "إيقاف", "start": "تشغيل", "reload": "إعادة تحميل"}
            return {"status": "success", "message": f"تمت {act_names.get(req.action, req.action)} الخدمة {srv} بنجاح"}
        else:
            raise HTTPException(status_code=500, detail=f"فشل الإجراء: {res.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء تنفيذ الأمر: {str(e)}")

@app.post("/api/system/process/kill")
async def kill_process(req: KillProcessRequest, sess: dict = Depends(verify_session)):
    target_pid = req.pid
    if target_pid <= 1:
        raise HTTPException(status_code=400, detail="محمي: لا يمكن إنهاء العملية الجذرية للنظام (PID 1)")
    if target_pid == os.getpid():
        raise HTTPException(status_code=400, detail="محمي: لا يمكن إنهاء عملية لوحة التحكم الحالية")
        
    try:
        proc = psutil.Process(target_pid)
        proc_name = proc.name()
        proc.kill()
        return {"status": "success", "message": f"تم إنهاء العملية {proc_name} (PID: {target_pid}) بنجاح"}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="العملية غير موجودة أو انتهت بالفعل")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="لا تملك الصلاحية الكافية لإنهاء هذه العملية")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل إنهاء العملية: {str(e)}")

@app.post("/api/system/clean")
async def clean_system(sess: dict = Depends(verify_session)):
    mem_before = psutil.virtual_memory().available
    disk_before = psutil.disk_usage('/').free
    
    actions_taken = []
    
    # 1. Sync and drop filesystem caches
    try:
        subprocess.run(["sync"], check=False)
        with open("/proc/sys/vm/drop_caches", "w") as f:
            f.write("3\n")
        actions_taken.append("تفريغ كاش الذاكرة والمخزن المؤقت (Drop Memory Caches)")
    except Exception as e:
        pass
        
    # 2. Vacuum systemd journals older than 2 days or > 40MB
    try:
        subprocess.run(["journalctl", "--vacuum-time=2d", "--vacuum-size=40M"], capture_output=True)
        actions_taken.append("تنظيف وضغط سجلات النظام القديمة (Systemd Journal Vacuum)")
    except Exception:
        pass
        
    # 3. Clean APT packages cache & temp files
    try:
        subprocess.run(["apt-get", "clean"], capture_output=True)
        actions_taken.append("تنظيف كاش حزم التحديثات (APT Package Cache Clean)")
    except Exception:
        pass
        
    # 4. Clean old /tmp files (safe delete files older than 3 days)
    try:
        subprocess.run(["find", "/tmp", "-type", "f", "-atime", "+3", "-delete"], capture_output=True)
        actions_taken.append("مسح الملفات المؤقتة القديمة في /tmp")
    except Exception:
        pass

    mem_after = psutil.virtual_memory().available
    disk_after = psutil.disk_usage('/').free
    
    ram_freed_mb = round((mem_after - mem_before) / (1024 * 1024), 1)
    if ram_freed_mb < 0:
        ram_freed_mb = 0.0
    disk_freed_mb = round((disk_after - disk_before) / (1024 * 1024), 1)
    if disk_freed_mb < 0:
        disk_freed_mb = 0.0
        
    return {
        "status": "success",
        "ram_freed_mb": ram_freed_mb,
        "disk_freed_mb": disk_freed_mb,
        "actions": actions_taken,
        "current_ram_percent": psutil.virtual_memory().percent,
        "current_disk_percent": psutil.disk_usage('/').percent
    }

# --- FILE MANAGER API ---
PANEL_DIR = Path(__file__).parent.resolve()

def is_path_hidden(p: Path) -> bool:
    try:
        resolved = p.resolve()
        return resolved == PANEL_DIR or PANEL_DIR in resolved.parents
    except:
        return False

@app.get("/api/files/list")
async def list_files(path: str = "/root", sess: dict = Depends(verify_session)):
    target_path = Path(path).resolve()
    if is_path_hidden(target_path):
        raise HTTPException(status_code=403, detail="هذا المجلد محمي ومخفي لأسباب أمنية")
        
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail="المسار غير موجود أو ليس مجلداً")
    
    items = []
    try:
        with os.scandir(str(target_path)) as entries:
            for entry in entries:
                try:
                    if is_path_hidden(Path(entry.path)):
                        continue
                    
                    stat = entry.stat(follow_symlinks=False)
                    is_dir = entry.is_dir(follow_symlinks=False)
                    is_symlink = entry.is_symlink()
                    size = stat.st_size if not is_dir else 0
                    mtime = stat.st_mtime
                    mode = oct(stat.st_mode)[-4:]
                    items.append({
                        "name": entry.name,
                        "path": str(Path(entry.path).resolve()) if not is_symlink else entry.path,
                        "is_dir": is_dir,
                        "is_symlink": is_symlink,
                        "size": size,
                        "mtime": mtime,
                        "permissions": mode,
                        "ext": Path(entry.name).suffix.lower() if not is_dir else ""
                    })
                except Exception:
                    continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="لا تملك صلاحية للوصول لهذا المجلد")

    # Sort directories first, then alphabetically
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    parent = str(target_path.parent) if str(target_path) != "/" else None
    return {
        "current_path": str(target_path),
        "parent_path": parent,
        "items": items
    }

@app.get("/api/files/read")
async def read_file(path: str, sess: dict = Depends(verify_session)):
    target_path = Path(path).resolve()
    if is_path_hidden(target_path):
        raise HTTPException(status_code=403, detail="هذا المسار محمي ومخفي لأسباب أمنية")
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    
    # Limit max editable size to 10MB to protect browser
    if target_path.stat().st_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="الملف كبير جداً للتحرير المباشر (أكبر من 10MB)")
    
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "path": str(target_path),
            "name": target_path.name,
            "content": content,
            "size": target_path.stat().st_size
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="الملف ثنائي (Binary) ولا يمكن تحريره كنص")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ أثناء قراءة الملف: {str(e)}")

@app.post("/api/files/save")
async def save_file(req: FileSaveRequest, sess: dict = Depends(verify_session)):
    target_path = Path(req.path).resolve()
    if is_path_hidden(target_path):
        raise HTTPException(status_code=403, detail="هذا المسار محمي ومخفي لأسباب أمنية")
    try:
        # Create backup if file exists
        if target_path.exists():
            pass
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "message": "تم حفظ الملف بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل حفظ الملف: {str(e)}")

@app.get("/api/files/download")
async def download_file(path: str, sess: dict = Depends(verify_session)):
    target_path = Path(path).resolve()
    if is_path_hidden(target_path):
        raise HTTPException(status_code=403, detail="هذا المسار محمي ومخفي لأسباب أمنية")
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    return FileResponse(
        path=str(target_path),
        filename=target_path.name,
        media_type='application/octet-stream'
    )

@app.get("/api/files/download_folder")
async def download_folder(path: str, sess: dict = Depends(verify_session)):
    target_path = Path(path).resolve()
    if is_path_hidden(target_path):
        raise HTTPException(status_code=403, detail="هذا المسار محمي ومخفي لأسباب أمنية")
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail="المجلد غير موجود")
    
    def iter_zip():
        proc = subprocess.Popen(
            ["zip", "-r", "-", "."],
            cwd=str(target_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        while True:
            chunk = proc.stdout.read(8192)
            if not chunk:
                break
            yield chunk
        proc.wait()

    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{target_path.name}.zip"'}
    )

@app.post("/api/files/upload")
async def upload_file(
    destination: str = Form(...),
    files: List[UploadFile] = File(...),
    sess: dict = Depends(verify_session)
):
    target_dir = Path(destination).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=404, detail="مجلد الوجهة غير موجود")
    
    uploaded = []
    for file in files:
        safe_name = os.path.basename(file.filename or "uploaded_file")
        if not safe_name or safe_name in [".", ".."]:
            continue
        dest_file = target_dir / safe_name
        try:
            with open(dest_file, "wb") as f:
                shutil.copyfileobj(file.file, f)
            uploaded.append(safe_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"فشل رفع الملف {safe_name}: {str(e)}")
        finally:
            await file.close()
            
    return {"status": "success", "uploaded": uploaded}

@app.post("/api/files/create")
async def create_item(req: CreateItemRequest, sess: dict = Depends(verify_session)):
    parent = Path(req.parent_path).resolve()
    # Strip path separators from item name to prevent traversal
    safe_name = os.path.basename(req.name.strip())
    if not safe_name or safe_name in [".", ".."]:
        raise HTTPException(status_code=400, detail="اسم العنصر غير صالح")
    target = parent / safe_name
    if target.exists():
        raise HTTPException(status_code=400, detail="الاسم موجود مسبقاً")
    
    try:
        if req.is_dir:
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.touch()
        return {"status": "success", "path": str(target)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الإنشاء: {str(e)}")

@app.post("/api/files/rename")
async def rename_item(req: RenameItemRequest, sess: dict = Depends(verify_session)):
    old_p = Path(req.old_path).resolve()
    if is_path_hidden(old_p):
        raise HTTPException(status_code=403, detail="هذا المسار محمي")
    new_p = Path(req.new_path).resolve()
    if is_path_hidden(new_p):
        raise HTTPException(status_code=403, detail="هذا المسار محمي")
    if not old_p.exists():
        raise HTTPException(status_code=404, detail="الملف الأصلي غير موجود")
    if new_p.exists():
        raise HTTPException(status_code=400, detail="الاسم الجديد موجود مسبقاً")
    
    try:
        old_p.rename(new_p)
        return {"status": "success", "new_path": str(new_p)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل إعادة التسمية: {str(e)}")

@app.post("/api/files/delete")
async def delete_item(req: DeleteItemRequest, sess: dict = Depends(verify_session)):
    target = Path(req.path).resolve()
    if is_path_hidden(target):
        raise HTTPException(status_code=403, detail="هذا المسار محمي")
    if not target.exists():
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    
    protected_roots = {
        "/", "/root", "/etc", "/var", "/usr", "/home", "/bin", "/sbin", 
        "/lib", "/lib64", "/boot", "/dev", "/proc", "/sys", "/srv", "/opt"
    }
    if str(target) in protected_roots:
        raise HTTPException(status_code=400, detail="محمي: لا يمكن حذف المجلدات الجذرية الحساسة للنظام")
        
    try:
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(str(target))
        else:
            target.unlink()
        return {"status": "success", "message": "تم الحذف بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الحذف: {str(e)}")

@app.post("/api/files/chmod")
async def chmod_item(req: ChmodRequest, sess: dict = Depends(verify_session)):
    target = Path(req.path).resolve()
    if is_path_hidden(target):
        raise HTTPException(status_code=403, detail="هذا المسار محمي")
    if not target.exists():
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    try:
        mode = int(req.permissions, 8)
        target.chmod(mode)
        return {"status": "success", "message": "تم تعديل الصلاحيات بنجاح"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل تعديل الصلاحيات: {str(e)}")

@app.post("/api/files/compress")
async def compress_item(req: CompressRequest, sess: dict = Depends(verify_session)):
    target = Path(req.path).resolve()
    if is_path_hidden(target):
        raise HTTPException(status_code=403, detail="هذا المسار محمي")
    if not target.exists():
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    try:
        zip_path = str(target.with_name(target.name + ".zip"))
        subprocess.Popen(
            ["zip", "-r", zip_path, target.name],
            cwd=str(target.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # We start it asynchronously and return success, since large folders might take a while.
        return {"status": "success", "message": "بدأ ضغط المجلد في الخلفية"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل بدء الضغط: {str(e)}")

# --- PERSISTENT PTY TERMINAL MANAGEMENT ---
class PersistentPtySession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.master_fd = None
        self.pid = None
        self.scrollback = bytearray()
        self.max_scrollback = 512 * 1024  # 512 KB
        self.websockets = set()
        self.reader_task = None
        self.is_running = False
        self.last_activity = time.time()

    def spawn(self):
        master_fd, slave_fd = pty.openpty()
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["LANG"] = "en_US.UTF-8"
        env["LC_ALL"] = "en_US.UTF-8"
        env["HOME"] = "/root"
        
        pid = os.fork()
        if pid == 0:
            os.close(master_fd)
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            if slave_fd > 2:
                os.close(slave_fd)
            shell = os.environ.get("SHELL", "/bin/bash")
            os.execvpe(shell, [shell, "-l"], env)
            sys.exit(0)
        else:
            os.close(slave_fd)
            self.master_fd = master_fd
            self.pid = pid
            self.is_running = True
            self.last_activity = time.time()
            self.reader_task = asyncio.create_task(self._read_loop())

    def is_alive(self):
        if not self.is_running or not self.pid:
            return False
        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid == self.pid:
                self.is_running = False
                return False
            os.kill(self.pid, 0)
            return True
        except Exception:
            self.is_running = False
            return False

    async def _read_loop(self):
        import select
        loop = asyncio.get_running_loop()
        while self.is_running and self.master_fd:
            try:
                r, _, _ = await loop.run_in_executor(None, select.select, [self.master_fd], [], [], 1.0)
                if not r:
                    continue
                try:
                    data = os.read(self.master_fd, 8192)
                    if data:
                        self.last_activity = time.time()
                        self.scrollback.extend(data)
                        if len(self.scrollback) > self.max_scrollback:
                            self.scrollback = self.scrollback[-self.max_scrollback:]
                            
                        dead_ws = []
                        for ws in list(self.websockets):
                            try:
                                await ws.send_bytes(data)
                            except Exception:
                                dead_ws.append(ws)
                        for dws in dead_ws:
                            self.websockets.discard(dws)
                except (BlockingIOError, InterruptedError):
                    pass
                except OSError:
                    break
            except asyncio.CancelledError:
                break
            except Exception:
                break
        self.is_running = False

    async def attach(self, websocket: WebSocket):
        self.websockets.add(websocket)
        # Send full previous screen & output history so session state is 100% restored
        if self.scrollback:
            try:
                await websocket.send_bytes(bytes(self.scrollback))
            except Exception:
                pass

    def detach(self, websocket: WebSocket):
        self.websockets.discard(websocket)

    def write(self, data: bytes):
        if self.is_running and self.master_fd:
            try:
                os.write(self.master_fd, data)
                self.last_activity = time.time()
            except Exception:
                pass

    def resize(self, cols: int, rows: int):
        if self.is_running and self.master_fd:
            try:
                winsize = struct.pack("HHHH", int(rows), int(cols), 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass

    def terminate(self):
        self.is_running = False
        if self.reader_task:
            self.reader_task.cancel()
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except Exception:
                pass
            self.master_fd = None
        if self.pid:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
            except Exception:
                pass
            self.pid = None

class TerminalSessionStore:
    def __init__(self):
        self.sessions = {}

    def get_or_create(self, session_id: str) -> PersistentPtySession:
        sess = self.sessions.get(session_id)
        if not sess or not sess.is_alive():
            if sess:
                sess.terminate()
            sess = PersistentPtySession(session_id)
            sess.spawn()
            self.sessions[session_id] = sess
        return sess

    def reset_session(self, session_id: str) -> PersistentPtySession:
        sess = self.sessions.get(session_id)
        if sess:
            sess.terminate()
        sess = PersistentPtySession(session_id)
        sess.spawn()
        self.sessions[session_id] = sess
        return sess

TERMINAL_MANAGER = TerminalSessionStore()

@app.post("/api/terminal/reset")
async def reset_terminal_session(sess: dict = Depends(verify_session)):
    session_id = "default_user_session"
    TERMINAL_MANAGER.reset_session(session_id)
    return {"status": "success", "message": "تمت إعادة تعيين جلسة الطرفية وبدء صدفة جديدة"}

# --- PTY TERMINAL WEBSOCKET (PERSISTENT) ---
@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket, token: Optional[str] = None):
    # Verify auth via query param token or cookie
    auth_token = token
    if not auth_token:
        cookies = websocket.cookies
        auth_token = cookies.get("session_token")
        
    if not auth_token or auth_token not in SESSION_STORE:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    session_id = "default_user_session"
    pty_session = TERMINAL_MANAGER.get_or_create(session_id)
    await pty_session.attach(websocket)

    import json
    try:
        while True:
            message = await websocket.receive()
            if "text" in message:
                text_data = message["text"]
                if text_data == "__ping__":
                    await websocket.send_text("__pong__")
                    continue
                if text_data.startswith("{") and "resize" in text_data:
                    try:
                        parsed = json.loads(text_data)
                        if "resize" in parsed:
                            cols, rows = parsed["resize"]
                            pty_session.resize(int(cols), int(rows))
                    except Exception:
                        pass
                else:
                    pty_session.write(text_data.encode("utf-8", errors="ignore"))
            elif "bytes" in message:
                pty_session.write(message["bytes"])
    except (WebSocketDisconnect, asyncio.CancelledError, RuntimeError):
        pass
    finally:
        # DO NOT KILL BASH! Simply detach the WebSocket so the session stays alive!
        pty_session.detach(websocket)

# ==============================================================================
# 🛡️ 1. SYSTEM FAIL2BAN & UFW FIREWALL MANAGEMENT API
# ==============================================================================

class Fail2banActionRequest(BaseModel):
    ip: str
    jail: Optional[str] = "sshd"

class UfwRuleRequest(BaseModel):
    action: str  # allow, deny, delete
    target: str

@app.get("/api/security/fail2ban")
async def get_fail2ban_system_status(sess: dict = Depends(verify_session)):
    try:
        status_proc = await asyncio.to_thread(
            subprocess.run, ["fail2ban-client", "status"],
            capture_output=True, text=True, timeout=5
        )
        jails = []
        for line in status_proc.stdout.splitlines():
            if "Jail list:" in line:
                raw_list = line.split("Jail list:")[1].strip()
                if raw_list:
                    jails = [j.strip() for j in raw_list.split(",") if j.strip()]

        jail_details = {}
        all_banned_ips = []
        for jail in jails:
            jproc = await asyncio.to_thread(
                subprocess.run, ["fail2ban-client", "status", jail],
                capture_output=True, text=True, timeout=5
            )
            banned_list = []
            curr_banned = 0
            total_banned = 0
            curr_failed = 0
            total_failed = 0
            for jline in jproc.stdout.splitlines():
                if "Currently banned:" in jline:
                    try: curr_banned = int(jline.split("Currently banned:")[1].strip())
                    except: pass
                elif "Total banned:" in jline:
                    try: total_banned = int(jline.split("Total banned:")[1].strip())
                    except: pass
                elif "Currently failed:" in jline:
                    try: curr_failed = int(jline.split("Currently failed:")[1].strip())
                    except: pass
                elif "Total failed:" in jline:
                    try: total_failed = int(jline.split("Total failed:")[1].strip())
                    except: pass
                elif "Banned IP list:" in jline:
                    b_raw = jline.split("Banned IP list:")[1].strip()
                    if b_raw:
                        banned_list = [ip.strip() for ip in b_raw.split() if ip.strip()]
            
            jail_details[jail] = {
                "currently_banned": curr_banned,
                "total_banned": total_banned,
                "currently_failed": curr_failed,
                "total_failed": total_failed,
                "banned_ips": banned_list
            }
            for ip in banned_list:
                all_banned_ips.append({"ip": ip, "jail": jail})

        ufw_proc = await asyncio.to_thread(
            subprocess.run, ["ufw", "status", "numbered"],
            capture_output=True, text=True, timeout=5
        )
        ufw_status_lines = [l.strip() for l in ufw_proc.stdout.splitlines() if l.strip()]

        return {
            "status": "success",
            "jails": jail_details,
            "all_banned_ips": all_banned_ips,
            "total_system_banned": len(all_banned_ips),
            "ufw": {
                "active": "active" in ufw_proc.stdout.lower(),
                "output": ufw_status_lines
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "jails": {}, "all_banned_ips": []}

@app.post("/api/security/fail2ban/unban")
async def unban_fail2ban_ip(req: Fail2banActionRequest, sess: dict = Depends(verify_session)):
    ip = req.ip.strip()
    jail = req.jail or "sshd"
    if not re.match(r"^[\da-fA-F:\.]+$", ip):
        raise HTTPException(status_code=400, detail="عنوان IP غير صالح")
    
    cmd = ["fail2ban-client", "unban", ip] if jail == "all" else ["fail2ban-client", "set", jail, "unbanip", ip]
    proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=5)
    
    if proc.returncode == 0:
        return {"status": "success", "message": f"تم فك حظر {ip} بنجاح من {jail}"}
    else:
        proc2 = await asyncio.to_thread(subprocess.run, ["fail2ban-client", "unban", ip], capture_output=True, text=True, timeout=5)
        return {"status": "success", "message": f"تمت معالجة فك الحظر: {proc.stdout or proc2.stdout or 'تم الإجراء'}"}

@app.post("/api/security/fail2ban/ban")
async def ban_fail2ban_ip(req: Fail2banActionRequest, sess: dict = Depends(verify_session)):
    ip = req.ip.strip()
    jail = req.jail or "sshd"
    if not re.match(r"^[\da-fA-F:\.]+$", ip):
        raise HTTPException(status_code=400, detail="عنوان IP غير صالح")
    proc = await asyncio.to_thread(subprocess.run, ["fail2ban-client", "set", jail, "banip", ip], capture_output=True, text=True, timeout=5)
    return {"status": "success", "message": f"تم حظر {ip} بنجاح في سجن {jail}"}

# ==============================================================================
# 🤖 2. TELEGRAM BOTS & APPLICATIONS MANAGER API
# ==============================================================================

DEFAULT_BOTS_REGISTRY = []

class BotActionRequest(BaseModel):
    bot_id: str
    action: str  # start, stop, restart


class WebhookReq(BaseModel):
    token: str
    url: str = ""

class BotRegisterRequest(BaseModel):
    bot_id: str
    name: str
    script: str
    venv: str = ""
    cwd: str = ""
    log: str = ""
    type: str = "python"
    webhook_url: str = ""
    bot_token: str = ""

class AnalyzeReq(BaseModel):
    file_path: str
@app.post("/api/bots/webhook/set")
async def set_webhook(req: WebhookReq, sess: dict = Depends(verify_session)):
    import json, urllib.request, urllib.parse, urllib.error
    tg_url = f"https://api.telegram.org/bot{req.token}/setWebhook?url={urllib.parse.quote(req.url)}"
    try:
        req_obj = urllib.request.Request(tg_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_obj, timeout=10) as response:
            res = json.loads(response.read().decode())
            return {"status": "success", "result": res}
    except urllib.error.URLError as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/bots/webhook/delete")
async def delete_webhook(req: WebhookReq, sess: dict = Depends(verify_session)):
    import json, urllib.request, urllib.error
    tg_url = f"https://api.telegram.org/bot{req.token}/deleteWebhook?drop_pending_updates=true"
    try:
        req_obj = urllib.request.Request(tg_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_obj, timeout=10) as response:
            res = json.loads(response.read().decode())
            return {"status": "success", "result": res}
    except urllib.error.URLError as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/bots/webhook/info")
async def get_webhook_info(req: WebhookReq, sess: dict = Depends(verify_session)):
    import json, urllib.request, urllib.error
    tg_url = f"https://api.telegram.org/bot{req.token}/getWebhookInfo"
    try:
        req_obj = urllib.request.Request(tg_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_obj, timeout=10) as response:
            res = json.loads(response.read().decode())
            return {"status": "success", "result": res}
    except urllib.error.URLError as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/bots/list")
async def get_bots_list(sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    registered = cfg.get("registered_bots", [])
    deleted_defaults = cfg.get("deleted_default_bots", [])
    all_bots = {b["id"]: b for b in DEFAULT_BOTS_REGISTRY if b["id"] not in deleted_defaults}
    for b in registered:
        all_bots[b["id"]] = b
        
    running_procs = {}
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
        try:
            cmdline = p.info.get('cmdline') or []
            cmd_str = " ".join(cmdline)
            for b_id, b_info in all_bots.items():
                script_name = Path(b_info["script"]).name
                if script_name in cmd_str and ("python" in cmd_str or b_info["script"] in cmd_str):
                    mem_mb = round(p.info['memory_info'].rss / (1024 * 1024), 1) if p.info.get('memory_info') else 0
                    uptime_secs = int(time.time() - p.info['create_time']) if p.info.get('create_time') else 0
                    
                    m, s = divmod(uptime_secs, 60)
                    h, m = divmod(m, 60)
                    d, h = divmod(h, 24)
                    uptime_str = f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m {s}s"
                    
                    running_procs[b_id] = {
                        "pid": p.info['pid'],
                        "cpu_percent": p.info.get('cpu_percent') or 0.0,
                        "memory_mb": mem_mb,
                        "uptime_seconds": uptime_secs,
                        "uptime_str": uptime_str
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    result = []
    for b_id, b_info in all_bots.items():
        is_running = b_id in running_procs
        proc_data = running_procs.get(b_id, {})
        result.append({
            "id": b_id,
            "name": b_info["name"],
            "script": b_info["script"],
            "venv": b_info.get("venv", "/usr/bin/python3"),
            "cwd": b_info.get("cwd", str(Path(b_info["script"]).parent)),
            "log": b_info.get("log", f"/root/{b_id}.log"),
            "is_running": is_running,
            "pid": proc_data.get("pid"),
            "cpu_percent": proc_data.get("cpu_percent", 0.0),
            "memory_mb": proc_data.get("memory_mb", 0.0),
            "uptime_str": proc_data.get("uptime_str", "—"),
            "type": b_info.get("type", "python"),
            "webhook_url": b_info.get("webhook_url", ""),
            "bot_token": b_info.get("bot_token", ""),
            "webhook_active": b_info.get("webhook_active", True)
        })

    return {"status": "success", "bots": result}

@app.post("/api/bots/action")
async def execute_bot_action(req: BotActionRequest, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    registered = cfg.get("registered_bots", [])
    deleted_defaults = cfg.get("deleted_default_bots", [])
    all_bots = {b["id"]: b for b in DEFAULT_BOTS_REGISTRY if b["id"] not in deleted_defaults}
    for b in registered:
        all_bots[b["id"]] = b
        
    if req.bot_id not in all_bots:
        raise HTTPException(status_code=404, detail="البوت أو التطبيق غير موجود في السجل")
        
    b_info = all_bots[req.bot_id]
    script_path = b_info["script"]
    python_bin = b_info.get("venv") or "/usr/bin/python3"
    cwd = b_info.get("cwd") or str(Path(script_path).parent)
    log_path = b_info.get("log") or f"/root/{req.bot_id}.log"
    script_name = Path(script_path).name

    running_pids = []
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd_str = " ".join(p.info.get('cmdline') or [])
            if script_name in cmd_str and ("python" in cmd_str or "php" in cmd_str or script_path in cmd_str):
                running_pids.append(p.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    systemd_map = {
        "yms_bot": "yms_bot.service",
        "yms_app": "yms_flask.service",
        "shop_bot": "shop-bot.service"
    }

    
    if req.action == "delete":
        # Stop process first if running
        if req.bot_id in systemd_map:
            await asyncio.to_thread(subprocess.run, ["systemctl", "stop", systemd_map[req.bot_id]], check=False)
        elif running_pids:
            for pid in running_pids:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                except: pass
        
        # Remove from config
        new_registered = [b for b in registered if b["id"] != req.bot_id]
        cfg["registered_bots"] = new_registered
        
        # If it's a default bot, add it to deleted_default_bots
        default_ids = [b["id"] for b in DEFAULT_BOTS_REGISTRY]
        if req.bot_id in default_ids:
            deleted = cfg.get("deleted_default_bots", [])
            if req.bot_id not in deleted:
                deleted.append(req.bot_id)
            cfg["deleted_default_bots"] = deleted
            
        ConfigManager.save(cfg)
        return {"status": "success"}

    if req.action in ["stop", "restart"]:
        if req.bot_id in systemd_map:
            await asyncio.to_thread(subprocess.run, ["systemctl", "stop", systemd_map[req.bot_id]], check=False)
        elif running_pids:
            for pid in running_pids:
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    p.wait(timeout=3)
                except Exception:
                    try:
                        import os
                        os.kill(pid, 9)
                        p.wait(timeout=1)
                    except Exception:
                        pass
    # Webhook specific actions
    if b_info.get("webhook_url"):
        import urllib.request, json, urllib.parse
        token = b_info.get("bot_token", "")
        url = b_info.get("webhook_url", "")
        if req.action == "stop":
            tg_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
            try:
                urllib.request.urlopen(urllib.request.Request(tg_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
            except Exception: pass
            b_info["webhook_active"] = False
            ConfigManager.save(cfg)
            return {"status": "success", "message": "تم إيقاف الويبهوك بنجاح"}
        elif req.action in ["start", "restart"]:
            tg_url = f"https://api.telegram.org/bot{token}/setWebhook?url={urllib.parse.quote(url)}"
            try:
                urllib.request.urlopen(urllib.request.Request(tg_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
            except Exception: pass
            b_info["webhook_active"] = True
            ConfigManager.save(cfg)
            if req.action == "start":
                return {"status": "success", "message": "تم تفعيل الويبهوك بنجاح"}
                
    if req.action == "stop":
        return {"status": "success", "message": f"تم إيقاف {b_info['name']} بنجاح"}

    if req.action == "start" and running_pids:
        return {"status": "error", "message": "البوت يعمل بالفعل!"}
        
    if req.action in ["start", "restart"]:
        if req.bot_id in systemd_map:
            await asyncio.to_thread(subprocess.run, ["systemctl", "start", systemd_map[req.bot_id]], check=False)
        else:
            import shutil
            if not shutil.which(python_bin):
                if "php" in python_bin:
                    return {"status": "error", "message": f"إصدار {python_bin} غير مثبت على السيرفر! يرجى تثبيته أو اختيار إصدار متوفر."}
                python_bin = sys.executable or "/usr/bin/python3"
                
            with open(log_path, "w") as log_file:
                subprocess.Popen(
                    [python_bin, script_path],
                    cwd=cwd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
        await asyncio.sleep(0.6)
        return {"status": "success", "message": f"تم تشغيل {b_info['name']} بنجاح"}

    return {"status": "error", "message": "إجراء غير معروف"}

@app.get("/api/bots/logs")
async def get_bot_logs(bot_id: str, lines: int = 100, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    deleted_defaults = cfg.get("deleted_default_bots", [])
    all_bots = {b["id"]: b for b in DEFAULT_BOTS_REGISTRY if b["id"] not in deleted_defaults}
    for b in cfg.get("registered_bots", []):
        all_bots[b["id"]] = b
    if bot_id not in all_bots:
        raise HTTPException(status_code=404, detail="البوت غير مسجل")
    log_path = Path(all_bots[bot_id].get("log") or f"/root/{bot_id}.log")
    if not log_path.exists():
        return {"status": "success", "logs": "لا توجد سجلات بعد (الملف قيد الإنشاء)"}
    try:
        proc = await asyncio.to_thread(subprocess.run, ["tail", f"-n{lines}", str(log_path)], capture_output=True, text=True)
        return {"status": "success", "logs": proc.stdout}
    except Exception as e:
        return {"status": "error", "logs": str(e)}




class SetupVenvReq(BaseModel):
    script_path: str

@app.post("/api/bots/setup_venv")
async def setup_venv(req: SetupVenvReq, sess: dict = Depends(verify_session)):
    import os, subprocess
    script_dir = os.path.dirname(req.script_path)
    venv_dir = os.path.join(script_dir, ".venv")
    req_file = os.path.join(script_dir, "requirements.txt")
    
    if not os.path.exists(script_dir):
        return {"status": "error", "message": "المسار غير موجود"}
        
    try:
        # Create venv if not exists
        if not os.path.exists(venv_dir):
            await asyncio.to_thread(subprocess.run, ["python3", "-m", "venv", ".venv"], cwd=script_dir, check=True, capture_output=True)
            
        python_path = os.path.join(venv_dir, "bin", "python")
        pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Upgrade pip and install requirements
        await asyncio.to_thread(subprocess.run, [python_path, "-m", "pip", "install", "--upgrade", "pip"], cwd=script_dir, capture_output=True)
        
        req_file = os.path.join(script_dir, "requirements.txt")
        if os.path.exists(req_file):
            res = await asyncio.to_thread(subprocess.run, [pip_path, "install", "-r", "requirements.txt"], cwd=script_dir, capture_output=True, text=True)
            if res.returncode != 0:
                return {"status": "error", "message": f"فشل تثبيت المكاتب: {res.stderr}"}
                
        return {"status": "success", "message": "تم إعداد البيئة والمكاتب بنجاح!", "venv_path": python_path}
    except Exception as e:
        return {"status": "error", "message": f"حدث خطأ أثناء إعداد البيئة: {str(e)}"}

@app.post("/api/bots/analyze_python")
async def analyze_python(req: AnalyzeReq, sess: dict = Depends(verify_session)):
    import os, re
    path = req.file_path
    if not os.path.exists(path):
        return {"status": "error", "message": "الملف غير موجود"}
        
    script_dir = os.path.dirname(path)
    
    # Check for common venv names
    possible_venvs = [
        os.path.join(script_dir, ".venv", "bin", "python"),
        os.path.join(script_dir, "venv", "bin", "python"),
        os.path.join(script_dir, "env", "bin", "python"),
        os.path.join(script_dir, ".env", "bin", "python")
    ]
    
    found_venv = ""
    for v in possible_venvs:
        if os.path.exists(v):
            found_venv = v
            break
            
    # Check for requirements.txt
    req_file = os.path.join(script_dir, "requirements.txt")
    has_requirements = os.path.exists(req_file)
        
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content_raw = f.read()
    
    token_match = re.search(r"(\d{8,12}:[a-zA-Z0-9_-]{34,})", content_raw)
    extracted_token = token_match.group(1) if token_match else ""
        
    return {
        "status": "success", 
        "venv": found_venv, 
        "has_requirements": has_requirements,
        "token": extracted_token
    }


@app.post("/api/bots/analyze_php")
async def analyze_php(req: AnalyzeReq, sess: dict = Depends(verify_session)):
    import os, re
    path = req.file_path
    if not os.path.exists(path):
        return {"status": "error", "message": "الملف غير موجود"}
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content_raw = f.read()
        content = content_raw.lower()
    
    is_webhook = False
    is_polling = False
    
    if "php://input" in content or "setwebhook" in content or "$_server" in content:
        is_webhook = True
    if "getupdates" in content or ("while" in content and "sleep" in content):
        is_polling = True
        
    mode = "unknown"
    if is_webhook and is_polling: mode = "both"
    elif is_webhook: mode = "webhook"
    elif is_polling: mode = "polling"
    
    # Extract token
    token_match = re.search(r"(\d{8,12}:[a-zA-Z0-9_-]{34,})", content_raw)
    extracted_token = token_match.group(1) if token_match else ""
        
    return {"status": "success", "mode": mode, "token": extracted_token}

@app.post("/api/bots/register")
async def register_custom_bot(req: BotRegisterRequest, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    if "registered_bots" not in cfg:
        cfg["registered_bots"] = []
    
    bot_id = re.sub(r"[^a-zA-Z0-9_]", "_", req.name.lower())
    new_entry = {
        "id": req.bot_id,
        "name": req.name,
        "script": req.script,
        "venv": req.venv or "/usr/bin/python3",
        "cwd": req.cwd or str(Path(req.script).parent),
        "log": req.log or f"/root/{req.bot_id}.log",
        "type": req.type,
        "webhook_url": req.webhook_url,
        "bot_token": req.bot_token
    }
    cfg["registered_bots"] = [b for b in cfg["registered_bots"] if b["id"] != bot_id]
    cfg["registered_bots"].append(new_entry)
    ConfigManager.save(cfg)
    return {"status": "success", "message": f"تم تسجيل {req.name} بنجاح", "bot": new_entry}

# ==============================================================================
# 💾 3. BACKUP & RESTORE MANAGER API
# ==============================================================================

BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

class BackupCreateRequest(BaseModel):
    preset: str  # shop, yms, databases, server_panel, custom
    custom_path: Optional[str] = None
    name: Optional[str] = None

@app.get("/api/backups/list")
async def list_backups(sess: dict = Depends(verify_session)):
    backups = []
    for folder in [BACKUP_DIR, Path("/root/shop-backups")]:
        if folder.exists():
            for item in folder.glob("**/*"):
                if item.is_file() and item.suffix in [".gz", ".zip", ".tar", ".tgz", ".db", ".sqlite"]:
                    stat = item.stat()
                    backups.append({
                        "filename": item.name,
                        "filepath": str(item),
                        "size_bytes": stat.st_size,
                        "size_str": f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size > 1024*1024 else f"{stat.st_size / 1024:.1f} KB",
                        "created_at": stat.st_mtime,
                        "created_str": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                    })
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return {"status": "success", "backups": backups}

@app.post("/api/backups/create")
async def create_backup(req: BackupCreateRequest, sess: dict = Depends(verify_session)):
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    preset_paths = {
        "server_panel": (str(BASE_DIR), f"backup_panel_{timestamp}.tar.gz"),
    }
    
    if req.preset == "databases":
        target_file = BACKUP_DIR / f"backup_databases_{timestamp}.tar.gz"
        db_files = list(Path("/root").glob("**/*.db")) + list(Path("/root").glob("**/*.sqlite*"))
        valid_dbs = [str(f) for f in db_files if ".gemini" not in str(f) and f.is_file()]
        if not valid_dbs:
            raise HTTPException(status_code=400, detail="لم يتم العثور على ملفات قواعد بيانات")
        cmd = ["tar", "-czf", str(target_file)] + valid_dbs
        proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"status": "success", "message": f"تم إنشاء نسخة احتياطية لقواعد البيانات بنجاح: {target_file.name}"}
        else:
            raise HTTPException(status_code=500, detail=f"فشل إنشاء النسخة: {proc.stderr}")

    elif req.preset in preset_paths:
        src_path, filename = preset_paths[req.preset]
        target_file = BACKUP_DIR / filename
        cmd = ["tar", "--exclude=venv", "--exclude=.venv", "--exclude=__pycache__", "--exclude=.git", "-czf", str(target_file), src_path]
        proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"status": "success", "message": f"تم إنشاء النسخة الاحتياطية بنجاح: {target_file.name}"}
        else:
            raise HTTPException(status_code=500, detail=f"فشل إنشاء النسخة: {proc.stderr}")

    elif req.preset == "custom" and req.custom_path:
        custom_p = Path(req.custom_path)
        if not custom_p.exists():
            raise HTTPException(status_code=404, detail="المسار المحدد غير موجود")
        filename = f"backup_custom_{timestamp}.tar.gz"
        target_file = BACKUP_DIR / filename
        cmd = ["tar", "--exclude=venv", "--exclude=.venv", "-czf", str(target_file), str(custom_p)]
        proc = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"status": "success", "message": f"تم إنشاء النسخة الاحتياطية بنجاح: {target_file.name}"}
        else:
            raise HTTPException(status_code=500, detail=f"فشل إنشاء النسخة: {proc.stderr}")
    else:
        raise HTTPException(status_code=400, detail="خيار نسخة احتياطية غير صالح")

@app.post("/api/backups/delete")
async def delete_backup(req: dict, sess: dict = Depends(verify_session)):
    filepath = req.get("filepath")
    if not filepath or not Path(filepath).exists():
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    p = Path(filepath).resolve()
    if not (str(p).startswith(str(BACKUP_DIR.resolve())) or str(p).startswith("/root/shop-backups")):
        raise HTTPException(status_code=403, detail="غير مصرح بحذف هذا الملف")
    p.unlink()
    return {"status": "success", "message": "تم حذف النسخة الاحتياطية بنجاح"}

@app.get("/api/backups/download")
async def download_backup(file: str, token: Optional[str] = None):
    if not token or token not in SESSION_STORE:
        raise HTTPException(status_code=401, detail="غير مصرح به")
    p = Path(file).resolve()
    if not p.exists() or not (str(p).startswith(str(BACKUP_DIR.resolve())) or str(p).startswith("/root/shop-backups")):
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    return FileResponse(str(p), filename=p.name, media_type="application/octet-stream")

# ==============================================================================
# 🗄️ 4. SQLITE DATABASE EXPLORER API
# ==============================================================================

class DbQueryRequest(BaseModel):
    db_path: str
    query: str
    limit: Optional[int] = 100

@app.get("/api/db/list")
async def list_databases(sess: dict = Depends(verify_session)):
    databases = []
    for item in Path("/root").glob("**/*"):
        if item.is_file() and (item.suffix in [".db", ".sqlite", ".sqlite3"] or "database" in item.name.lower()):
            if ".gemini" not in str(item):
                stat = item.stat()
                databases.append({
                    "name": item.name,
                    "path": str(item),
                    "size_str": f"{stat.st_size / (1024*1024):.2f} MB" if stat.st_size > 1024*1024 else f"{stat.st_size / 1024:.1f} KB",
                    "modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                })
    return {"status": "success", "databases": databases}

@app.get("/api/db/schema")
async def get_db_schema(db_path: str, sess: dict = Depends(verify_session)):
    p = Path(db_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="قاعدة البيانات غير موجودة")
    def fetch_schema(db_path):
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        schema_data = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}')")
            cols = [{"name": r[1], "type": r[2], "notnull": bool(r[3]), "pk": bool(r[5])} for r in cursor.fetchall()]
            cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
            schema_data[table] = {"columns": cols, "total_rows": cursor.fetchone()[0]}
        conn.close()
        return tables, schema_data

    try:
        tables, schema_data = await asyncio.to_thread(fetch_schema, p)
        return {"status": "success", "tables": tables, "schema": schema_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في قراءة قاعدة البيانات: {e}")

@app.post("/api/db/query")
async def execute_db_query(req: DbQueryRequest, sess: dict = Depends(verify_session)):
    p = Path(req.db_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="قاعدة البيانات غير موجودة")
    
    query = req.query.strip()
    is_select = query.upper().startswith("SELECT") or query.upper().startswith("PRAGMA")
    
    def execute_query(db_path, query_str, select_mode, limit):
        if select_mode:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        else:
            conn = sqlite3.connect(str(db_path))
            
        cursor = conn.cursor()
        start_t = time.time()
        cursor.execute(query_str)
        
        if select_mode:
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(limit or 100)
            elapsed = round((time.time() - start_t) * 1000, 2)
            conn.close()
            return {
                "status": "success",
                "is_select": True,
                "columns": columns,
                "rows": rows,
                "count": len(rows),
                "execution_ms": elapsed
            }
        else:
            conn.commit()
            changes = conn.total_changes
            elapsed = round((time.time() - start_t) * 1000, 2)
            conn.close()
            return {
                "status": "success",
                "is_select": False,
                "affected_rows": changes,
                "execution_ms": elapsed,
                "message": f"تم تنفيذ الاستعلام بنجاح (تأثر {changes} صف)"
            }

    try:
        return await asyncio.to_thread(execute_query, p, query, is_select, req.limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"خطأ في الاستعلام: {e}")

# ==============================================================================
# 📜 5. UNIFIED SYSTEM & SERVER LOG EXPLORER API
# ==============================================================================

LOG_SOURCES = {
    "nginx-access": {"name": "سجلات وصول Nginx (Access)", "path": "/var/log/nginx/access.log"},
    "nginx-error": {"name": "سجلات أخطاء Nginx (Errors)", "path": "/var/log/nginx/error.log"},
    "fail2ban": {"name": "سجلات الحظر Fail2Ban", "path": "/var/log/fail2ban.log"},
    "ssh-auth": {"name": "سجلات أمان وتوثيق SSH", "path": "/var/log/auth.log"},
    "system-dmesg": {"name": "سجلات نواة النظام (Kernel/Dmesg)", "path": "/var/log/kern.log"}
}

@app.get("/api/logs/sources")
async def get_log_sources(sess: dict = Depends(verify_session)):
    sources = []
    for k, v in LOG_SOURCES.items():
        exists = Path(v["path"]).exists()
        size_str = ""
        if exists:
            sz = Path(v["path"]).stat().st_size
            size_str = f"{sz / (1024*1024):.1f} MB" if sz > 1024*1024 else f"{sz / 1024:.0f} KB"
        sources.append({
            "key": k,
            "name": v["name"],
            "path": v["path"],
            "exists": exists,
            "size": size_str
        })
    return {"status": "success", "sources": sources}

@app.get("/api/logs/view")
async def view_system_log(source: str, lines: int = 150, filter_query: Optional[str] = None, sess: dict = Depends(verify_session)):
    if source not in LOG_SOURCES:
        raise HTTPException(status_code=404, detail="مصدر السجل غير موجود")
    log_info = LOG_SOURCES[source]
    log_path = Path(log_info["path"])
    if not log_path.exists():
        return {"status": "success", "lines": [], "message": "ملف السجل فارغ أو غير موجود حالياً"}
    
    try:
        proc = await asyncio.to_thread(subprocess.run, ["tail", f"-n{lines}", str(log_path)], capture_output=True, text=True)
        raw_lines = proc.stdout.splitlines()
        if filter_query:
            q = filter_query.lower()
            raw_lines = [l for l in raw_lines if q in l.lower()]
        return {"status": "success", "lines": raw_lines, "source": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 🔔 6. TELEGRAM NOTIFICATIONS & ALERTS API
# ==============================================================================

def send_telegram_alert_sync(text: str) -> bool:
    cfg = ConfigManager.load()
    bot_token = cfg.get("telegram_bot_token")
    chat_id = cfg.get("telegram_chat_id")
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=6) as response:
            return response.status == 200
    except Exception as e:
        print(f"[Telegram Alert Error] {e}")
        return False

async def send_telegram_alert(text: str) -> bool:
    return await asyncio.to_thread(send_telegram_alert_sync, text)

class TelegramSettingsRequest(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    alerts_enabled: bool
    alert_on_attack: Optional[bool] = True
    alert_on_bot_crash: Optional[bool] = True
    alert_on_high_load: Optional[bool] = True

@app.get("/api/settings/telegram")
async def get_telegram_settings(sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    token = cfg.get("telegram_bot_token", "")
    masked_token = (token[:6] + "..." + token[-4:]) if len(token) > 10 else ("مضبوط" if token else "")
    return {
        "status": "success",
        "has_token": bool(token),
        "masked_token": masked_token,
        "chat_id": cfg.get("telegram_chat_id", ""),
        "alerts_enabled": cfg.get("telegram_alerts_enabled", False),
        "alert_on_attack": cfg.get("alert_on_attack", True),
        "alert_on_bot_crash": cfg.get("alert_on_bot_crash", True),
        "alert_on_high_load": cfg.get("alert_on_high_load", True)
    }

@app.post("/api/settings/telegram")
async def save_telegram_settings(req: TelegramSettingsRequest, sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    if req.bot_token and not req.bot_token.startswith("..."):
        cfg["telegram_bot_token"] = req.bot_token.strip()
    if req.chat_id:
        cfg["telegram_chat_id"] = req.chat_id.strip()
    cfg["telegram_alerts_enabled"] = req.alerts_enabled
    cfg["alert_on_attack"] = req.alert_on_attack
    cfg["alert_on_bot_crash"] = req.alert_on_bot_crash
    cfg["alert_on_high_load"] = req.alert_on_high_load
    ConfigManager.save(cfg)
    return {"status": "success", "message": "تم حفظ إعدادات تنبيهات تليجرام بنجاح"}

@app.post("/api/settings/telegram/test")
async def test_telegram_alert(sess: dict = Depends(verify_session)):
    cfg = ConfigManager.load()
    bot_token = cfg.get("telegram_bot_token")
    chat_id = cfg.get("telegram_chat_id")
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="يرجى إدخال Bot Token و Chat ID أولاً")
    
    msg = (
        "🔔 <b>[لوحة تحكم السيرفر - تجربة التنبيهات]</b>\n\n"
        "✅ تم توصيل وتفعيل تنبيهات السيرفر بنجاح عبر تليجرام!\n"
        f"⏰ <b>الوقت:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"🖥️ <b>اسم السيرفر:</b> {platform.node()}\n"
        f"🛡️ <b>الحالة:</b> جميع أنظمة الحماية تعمل بأعلى كفاءة."
    )
    ok = await send_telegram_alert(msg)
    if ok:
        return {"status": "success", "message": "تم إرسال رسالة التجربة إلى تليجرام بنجاح! تفقد محادثتك."}
    else:
        raise HTTPException(status_code=500, detail="فشل إرسال التنبيه، تأكد من صحة الـ Token و Chat ID وبدء محادثة مع البوت (/start)")

# Mount static files
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_index():
    with open(str(STATIC_DIR / "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(
            content=f.read(),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=config.get("port", 8090), log_level="info")


# --- DOMAINS AND SSL ---
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

def generate_nginx_conf(req: DomainCreateRequest, has_ssl: bool = False):
    conf_lines = []
    
    location_block = []
    if req.type == "static":
        root = req.document_root or f"/var/www/{req.domain}"
        Path(root).mkdir(parents=True, exist_ok=True)
        location_block.append(f"    root {root};")
        location_block.append("    index index.html index.php;")
        location_block.append("    location / {")
        location_block.append("        try_files $uri $uri/ =404;")
        location_block.append("    }")
        
        # PHP support
        location_block.append("    location ~ \\.php$ {")
        location_block.append("        include snippets/fastcgi-php.conf;")
        # Dynamically find the PHP-FPM socket if available, default to 8.1
        location_block.append("        fastcgi_pass unix:/var/run/php/php-fpm.sock;")
        location_block.append("        # Note: A symlink or the exact version socket should be mapped to php-fpm.sock")
        location_block.append("    }")
    else:
        proxy = req.proxy_url or "http://127.0.0.1:8080"
        location_block.append("    location / {")
        location_block.append(f"        proxy_pass {proxy};")
        location_block.append("        proxy_set_header Host $host;")
        location_block.append("        proxy_set_header X-Real-IP $remote_addr;")
        location_block.append("        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
        location_block.append("        proxy_set_header X-Forwarded-Proto $scheme;")
        location_block.append("    }")

    conf_lines.append("server {")
    conf_lines.append("    listen 80;")
    conf_lines.append(f"    server_name {req.domain};")
    
    if has_ssl and req.force_https:
        conf_lines.append("    return 301 https://$host$request_uri;")
    else:
        conf_lines.extend(location_block)
    conf_lines.append("}")

    if has_ssl:
        conf_lines.append("")
        conf_lines.append("server {")
        conf_lines.append("    listen 443 ssl;")
        conf_lines.append(f"    server_name {req.domain};")
        conf_lines.append(f"    ssl_certificate /etc/letsencrypt/live/{req.domain}/fullchain.pem;")
        conf_lines.append(f"    ssl_certificate_key /etc/letsencrypt/live/{req.domain}/privkey.pem;")
        conf_lines.append("    include /etc/letsencrypt/options-ssl-nginx.conf;")
        conf_lines.append("    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;")
        conf_lines.extend(location_block)
        conf_lines.append("}")
    return "\n".join(conf_lines)


async def safe_nginx_reload():
    res = await asyncio.to_thread(subprocess.run, ["nginx", "-t"], capture_output=True, text=True)
    if res.returncode != 0:
        return False, res.stderr
    await asyncio.to_thread(subprocess.run, ["systemctl", "reload", "nginx"], check=True)
    return True, ""

@app.post("/api/domains/create")
async def create_domain_config(req: DomainCreateRequest, sess: dict = Depends(verify_session)):
    if not re.match(r"^[a-zA-Z0-9.-]+$", req.domain):
        return JSONResponse({"success": False, "error": "اسم النطاق غير صالح"})
        
    avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
    enabled_path = Path(f"/etc/nginx/sites-enabled/{req.domain}")
    
    conf = generate_nginx_conf(req, has_ssl=False)
    try:
        avail_path.write_text(conf)
        if not enabled_path.exists():
            enabled_path.symlink_to(avail_path)
            
        success, err = await safe_nginx_reload()
        if not success:
            avail_path.unlink()
            if enabled_path.exists(): enabled_path.unlink()
            return JSONResponse({"success": False, "error": f"خطأ في إعدادات Nginx: {err}"})
            
        return JSONResponse({"success": True, "message": f"تمت إضافة النطاق {req.domain} بنجاح."})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.post("/api/domains/edit")
async def edit_domain_config(req: DomainCreateRequest, sess: dict = Depends(verify_session)):
    if not re.match(r"^[a-zA-Z0-9.-]+$", req.domain):
        return JSONResponse({"success": False, "error": "اسم النطاق غير صالح"})
        
    avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
    enabled_path = Path(f"/etc/nginx/sites-enabled/{req.domain}")
    
    # Backup old config in case of failure
    old_conf = avail_path.read_text() if avail_path.exists() else ""
    
    # Check if SSL exists
    has_ssl = Path(f"/etc/letsencrypt/live/{req.domain}").exists()
    
    conf = generate_nginx_conf(req, has_ssl=has_ssl)

    try:
        avail_path.write_text(conf)
        if not enabled_path.exists():
            enabled_path.symlink_to(avail_path)
            
        success, err = await safe_nginx_reload()
        if not success:
            # Rollback
            if old_conf:
                avail_path.write_text(old_conf)
            else:
                avail_path.unlink()
                if enabled_path.exists(): enabled_path.unlink()
            return JSONResponse({"success": False, "error": f"خطأ في إعدادات Nginx، تم التراجع: {err}"})
            
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
        avail_path = Path(f"/etc/nginx/sites-available/{req.domain}")
        # Request SSL exactly for the requested domain to avoid DNS errors with 'www'
        cmd = ["certbot", "--nginx", "-d", req.domain, "--non-interactive", "--agree-tos", "--register-unsafely-without-email"]
        
        if avail_path.exists() and "return 301 https" in avail_path.read_text():
            cmd.append("--redirect")
            
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            await safe_nginx_reload()
            return JSONResponse({"success": True, "message": "تم إصدار/تجديد شهادة SSL بنجاح!"})
        else:
            err = result.stderr or result.stdout
            return JSONResponse({"success": False, "error": f"فشل تثبيت SSL: {err}"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

# --- PHP CGI PROXY FOR WEBHOOKS ---
from fastapi.responses import Response

@app.api_route("/{file_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def execute_php_webhook(request: Request, file_path: str):
    if not file_path.endswith(".php"):
        raise HTTPException(status_code=404, detail="Not Found")
        
    full_path = (Path("/root") / file_path).resolve()
    if not str(full_path).startswith("/root/"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File Not Found")
        
    body = await request.body()
    
    import os, subprocess, shutil
    env = os.environ.copy()
    env["REQUEST_METHOD"] = request.method
    env["CONTENT_TYPE"] = request.headers.get("content-type", "")
    env["CONTENT_LENGTH"] = str(len(body))
    env["SCRIPT_FILENAME"] = str(full_path)
    env["SCRIPT_NAME"] = f"/{file_path}"
    env["REDIRECT_STATUS"] = "200"
    
    php_cgi = shutil.which("php-cgi") or shutil.which("php-cgi8.4") or shutil.which("php-cgi8.2")
    if not php_cgi:
        return Response(content="PHP CGI not installed", status_code=500)
        
    proc = subprocess.Popen(
        [php_cgi],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(full_path.parent)
    )
    
    stdout, stderr = proc.communicate(input=body)
    
    try:
        header_text, res_body = stdout.split(b"\r\n\r\n", 1)
    except ValueError:
        try:
            header_text, res_body = stdout.split(b"\n\n", 1)
        except ValueError:
            return Response(content=stdout)
            
    return Response(content=res_body)

