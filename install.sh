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
CYAN="\e[36m"
MAGENTA="\e[35m"
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
apt-get install -y python3 python3-venv python3-pip nginx fail2ban ufw sqlite3 curl git psmisc php-cli php-cgi php-curl

# 3. إعداد مسار المشروع
INSTALL_DIR="/opt/curlHUB"
REPO_URL="https://github.com/mosap111/curlHUB---panel-.git"

echo -e "${YELLOW}[2/6] تحميل المشروع من GitHub...${RESET}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "المجلد موجود مسبقاً، سيتم تحديثه..."
    cd $INSTALL_DIR
    git pull
else
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

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

SERVER_IP=$(curl -s ifconfig.me || echo "YOUR_SERVER_IP")

clear
echo -e "${CYAN}"
cat << 'ART'
 $$$$$$\                      $$ |      $$ |  $$ |$$ |  $$ |$$$$$$$\  
$$  __$$\                     $$ |      $$ |  $$ |$$ |  $$ |$$  __$$\ 
$$ /  \__|$$\   $$\  $$$$$$\  $$ |      $$$$$$$$ |$$ |  $$ |$$ |  $$ |
$$ |      $$ |  $$ |$$  __$$\ $$ |      $$  __$$ |$$ |  $$ |$$$$$$$\ |
$$ |      $$ |  $$ |$$ |  \__|$$ |      $$ |  $$ |$$ |  $$ |$$  __$$\ 
$$ |  $$\ $$ |  $$ |$$ |      $$ |      $$ |  $$ |$$ |  $$ |$$ |  $$ |
\$$$$$$  |\$$$$$$  |$$ |      $$$$$$$$\ $$ |  $$ |\$$$$$$  |$$$$$$$  |
 \______/  \______/ \__|      \________|\__|  \__| \______/ \_______/ 
ART
echo -e "${RESET}"

echo -e "${GREEN}====================================================${RESET}"
echo -e "${GREEN}✅ تم التثبيت بنجاح! السيرفر الخاص بك الآن تحت إدارتك.${RESET}"
echo -e "${GREEN}====================================================${RESET}"
echo -e ""
echo -e "${YELLOW}🌐 رابط اللوحة:${RESET} ${CYAN}http://${SERVER_IP}${RESET}"
echo -e "${YELLOW}👤 اسم المستخدم:${RESET} ${CYAN}admin${RESET}"
echo -e "${YELLOW}🔑 كلمة المرور:${RESET} ${CYAN}admin123456${RESET}"
echo -e ""
echo -e "${MAGENTA}⚠️ هام: يرجى تغيير كلمة المرور من الإعدادات فور تسجيل الدخول!${RESET}"
echo -e "${GREEN}⚙️ لمراقبة السجلات لاحقاً:${RESET} journalctl -u server-panel -f"
echo -e "${GREEN}====================================================${RESET}"
