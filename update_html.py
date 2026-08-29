import re

html_path = "/root/server_panel/static/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

stats_html = """
                    <!-- Advanced Stats -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; padding: 20px 20px 0 20px;">
                        <div class="stat-pill" style="padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px;">
                            <span style="color: #94a3b8; font-size: 13px; margin-bottom: 5px;">إجمالي النطاقات</span>
                            <span id="stat-total-domains" style="font-size: 24px; font-weight: bold; color: #e2e8f0;">0</span>
                        </div>
                        <div class="stat-pill" style="padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2); border-radius: 12px;">
                            <span style="color: #4ade80; font-size: 13px; margin-bottom: 5px;">نطاقات محمية (SSL)</span>
                            <span id="stat-secured-domains" style="font-size: 24px; font-weight: bold; color: #4ade80;">0</span>
                        </div>
                        <div class="stat-pill" style="padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(234,179,8,0.1); border: 1px solid rgba(234,179,8,0.2); border-radius: 12px;">
                            <span style="color: #facc15; font-size: 13px; margin-bottom: 5px;">شهادات تنتهي قريباً</span>
                            <span id="stat-expiring-domains" style="font-size: 24px; font-weight: bold; color: #facc15;">0</span>
                        </div>
                    </div>
"""

# Insert stats before <div class="card-body">
if "<!-- Advanced Stats -->" not in content:
    content = content.replace('<div class="card-body">', stats_html + '\n                    <div class="card-body">', 1)

# Modify the Modal to include Force HTTPS toggle
force_https_html = """
                <div class="form-group" style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                    <label class="switch" style="margin:0;">
                        <input type="checkbox" id="domain-force-https">
                        <span class="slider round"></span>
                    </label>
                    <div style="display: flex; flex-direction: column;">
                        <span style="color: #e2e8f0; font-weight: bold;">فرض الاتصال الآمن (Force HTTPS)</span>
                        <span style="color: #64748b; font-size: 12px;">إعادة توجيه الزوار تلقائياً من HTTP إلى HTTPS</span>
                    </div>
                </div>
"""

if 'id="domain-force-https"' not in content:
    content = content.replace('</div>\n            <div class="modal-buttons"', force_https_html + '</div>\n            <div class="modal-buttons"')

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)
print("HTML updated.")
