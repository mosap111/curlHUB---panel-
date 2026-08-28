#!/bin/bash

# ==============================================================================
# أداة التثبيت التلقائي للوحة تحكم وإدارة السيرفر
# curlHUB - Auto Installation Script
# ==============================================================================

# ألوان للتنسيق
GREEN="\e[32m"
YELLOW="\e[33m"
RED="\e[31m"
BLUE="\e[34m"
RESET="\e[0m"

# 1. التحقق من صلاحيات الروت (Root)
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}الرجاء تشغيل السكريبت بصلاحيات الروت: sudo ./install.sh${RESET}"
  exit 1
fi

echo -e "${BLUE}🚀 بدء تثبيت لوحة تحكم السيرفر (curlHUB)...${RESET}"

# 2. تحديث النظام وتثبيت الحزم الأساسية
echo -e "${YELLOW}[1/6] تحديث الحزم وتثبيت المتطلبات الأساسية (Nginx, Python, Fail2ban)...${RESET}"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx fail2ban ufw sqlite3 curl git psmisc

# 3. إعداد مسار المشروع
# (لأغراض النشر المفتوح، استبدل النسخ برابط الاستنساخ من GitHub)
INSTALL_DIR="/opt/server_panel"

echo -e "${YELLOW}[2/6] إعداد مسار ومجلدات المشروع...${RESET}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "المجلد موجود مسبقاً في ${INSTALL_DIR}."
else
    # git clone https://github.com/USERNAME/server_panel.git $INSTALL_DIR
    cp -r /root/server_panel $INSTALL_DIR 2>/dev/null || echo -e "${RED}تحذير: المسار الأصلي غير موجود.${RESET}"
fi

cd $INSTALL_DIR

# 4. إعداد البيئة الافتراضية لبايثون
echo -e "${YELLOW}[3/6] إعداد بيئة بايثون وتثبيت المكتبات...${RESET}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

if [ ! -f "requirements.txt" ]; then
    cat <<REQ > requirements.txt
fastapi
uvicorn
websockets
psutil
python-multipart
REQ
fi
pip install -r requirements.txt

# 5. إعداد خدمة التشغيل الدائم (Systemd)
echo -e "${YELLOW}[4/6] إنشاء خدمة التشغيل التلقائي (server-panel.service)...${RESET}"
cat <<SVC > /etc/systemd/system/server-panel.service
[Unit]
Description=curlHUB
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
Restart=always

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable server-panel
systemctl restart server-panel

# 6. إعداد خادم الويب Nginx (Proxy)
echo -e "${YELLOW}[5/6] إعداد البروكسي العكسي عبر Nginx...${RESET}"
cat <<NGX > /etc/nginx/sites-available/server-panel
server {
    listen 80;
    server_name _; 

    location / {
        proxy_pass http://127.0.0.1:8090;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
NGX

ln -sf /etc/nginx/sites-available/server-panel /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

# 7. إعداد الحماية
echo -e "${YELLOW}[6/6] ضبط جدار الحماية (UFW) وبدء Fail2Ban...${RESET}"
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
systemctl enable fail2ban
systemctl start fail2ban

SERVER_IP=$(curl -s ifconfig.me || echo "SERVER_IP")

echo -e "${GREEN}====================================================${RESET}"
echo -e "${GREEN}✅ تم تثبيت وتشغيل لوحة التحكم بنجاح!${RESET}"
echo -e "${GREEN}🌐 رابط الدخول للوحة: http://${SERVER_IP}${RESET}"
echo -e "${GREEN}⚙️ مراقبة السجلات: journalctl -u server-panel -f${RESET}"
echo -e "${GREEN}====================================================${RESET}"
