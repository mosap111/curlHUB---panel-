import json

phrases = """0 حدث
0 سطر
0 نشطة
أدخل اسم المستخدم
أدوات الويبهوك لبوتات PHP
أهلاً بك مجدداً! قم بتسجيل الدخول للمتابعة
إجراءات
إجمالي المحاولات المحظورة
إجمالي النطاقات
إدارة النطاقات والشهادات (Domains & SSL)
إضافة نطاق جديد
إعادة الاتصال بالجلسة الحالية
إعادة توجيه الزوار تلقائياً من HTTP إلى HTTPS
إعادة فحص القواعد
إغلاق الملف
إلغاء وإيقاف الأمر الجاري (Ctrl+C / SIGINT)
إنهاء الجلسة الحالية وبدء جلسة نظيفة جديدة
إيقاف (يدوي)
اختر طريقة التشغيل المفضلة
اختر قاعدة البيانات:
استدعاء الأمر التالي (السهم لأسفل)
استدعاء الأمر السابق (السهم لأعلى)
استقبل إشعارات فورية على حسابك عند حدوث هجمات، توقف البوتات، أو ارتفاع استهلاك السيرفر.
استهلاك الذاكرة الافتراضية Swap
استهلاك الرام
استهلاك المعالج
استهلاك مساحة التخزين
اسم البرنامج / الأمر
اسم النطاق (مثال: example.com)
الإجراءات
الانتقال لبداية السطر (Ctrl+A)
الانتقال لنهاية السطر (Ctrl+E)
البرامج والعمليات
القائمة
المجلد السابق
المخزن المؤقت:
المسار / التوجيه
المسار: --
المنافذ المفتوحة (Ports)
المهام المنجزة:
النشطة حالياً:
النطاق
النطاقات والشهادات
النوع
بحث باسم البرنامج أو الـ PID...
بحث باسم الخدمة (مثل nginx, cron)...
بحث بالبورت أو اسم الخدمة...
بحث بالـ IP أو المسار أو الأداة...
بحث في المجلد الحالي...
بروكسي (توجيه لمنفذ، مثل البوتات)
تبديل المظهر (داكن/فاتح)
تحديث السجل
تحديث السجلات
تحديث القائمة
تحديث تلقائي:
تحديث حالة البوتات
تحريك المؤشر يميناً
تسجيل الخروج
تسجيل الدخول للسيرفر
تسجيل بوت أو تطبيق جديد
تسجيل تطبيق أو بوت جديد
تشغيل بنظام Webhook (الأسرع والأفضل)
تصفح وتحديد الملف
تعليق العملية بالخلفية (Ctrl+Z / SIGTSTP)
تغيير الثيم
تغيير اللغة
تغييرات غير محفوظة
تفريغ سجلات الأمان
تفريغ كاش الرام وتنظيف مخلفات النظام
تنظيف السيرفر
تنظيف كاش حزم التحديثات (APT Package Cache Clean)
تنفيذ الأمر (Enter)
جاري تحميل النطاقات...
جاري فحص العمليات النشطة...
جاري فحص المنافذ المفتوحة...
جاري فحص ورصد البوتات والتطبيقات قيد التشغيل...
حالة SSL
حالة جدار الحماية وسجون Fail2Ban في النظام (System Fail2Ban & UFW)
حظر يدوي (Manual)
حظر يدوي بواسطة المسؤول
حفظ (Ctrl+S)
حفظ النطاق
حفظ وتشغيل البوت
خروج / EOF (Ctrl+D)
درع الأمان & Fail2Ban
رابط التوجيه
رابط الويبهوك (Webhook URL)
سبب الحظر الأمني
سجل الهجمات ومحاولات التخمين والاختراق اللحظي (Live Attack Logs)
سجلات النواة (Kernel/Dmesg)
شهادات تنتهي قريباً
فخ مسارات حساسة (Honeypot)
فرض الاتصال الآمن (Force HTTPS)
كل 10 ثوانٍ
كل 3 ثوانٍ
كل التهديدات
كلمة المرور
كلمة المرور الحالية
لم يتم تنفيذ استعلام بعد
مثال: /root/my_bot/main.py
مثال: 123456789
مثال: 123456789:ABCdefGhIJKlmNoPQRstuVWXyz
مثال: 192.168.1.50
مثال: PHP Webhook Bot
مثال: Telegram Notify Bot
مثال: نشاط مشبوه وفحص غير مصرح
مجلد العمل (Working Directory)
مجلد جديد
محاولة فاشلة
مدة التشغيل:
مسار البيئة الافتراضية (Python Venv)
مسار الملفات (اختياري)
مسار ملف التشغيل (Script Path)
مستعرض ومحرر قواعد بيانات SQLite (Database Studio)
مسح الشاشة (Ctrl+L)
مصدر السجل:
معالجة وتصحيح الكلمات العربية وربط الحروف
ملء الشاشة
موقع ثابت / PHP (ملفات)
نطاقات محمية (SSL)
نوع النطاق
⚡ تسريع وتنظيف السيرفر""".split("\n")

manual_trans = {
    "0 حدث": "0 Events",
    "0 سطر": "0 Lines",
    "0 نشطة": "0 Active",
    "أدخل اسم المستخدم": "Enter Username",
    "أدوات الويبهوك لبوتات PHP": "PHP Webhook Tools",
    "أهلاً بك مجدداً! قم بتسجيل الدخول للمتابعة": "Welcome back! Login to continue",
    "إجراءات": "Actions",
    "إجمالي المحاولات المحظورة": "Total Blocked Attempts",
    "إجمالي النطاقات": "Total Domains",
    "إدارة النطاقات والشهادات (Domains & SSL)": "Domains & SSL Management",
    "إضافة نطاق جديد": "Add New Domain",
    "إعادة الاتصال بالجلسة الحالية": "Reconnect to session",
    "إعادة توجيه الزوار تلقائياً من HTTP إلى HTTPS": "Auto redirect HTTP to HTTPS",
    "إعادة فحص القواعد": "Rescan Rules",
    "إغلاق الملف": "Close File",
    "إلغاء وإيقاف الأمر الجاري (Ctrl+C / SIGINT)": "Cancel Command (Ctrl+C)",
    "إنهاء الجلسة الحالية وبدء جلسة نظيفة جديدة": "Terminate session",
    "إيقاف (يدوي)": "Stop (Manual)",
    "اختر طريقة التشغيل المفضلة": "Choose Run Method",
    "اختر قاعدة البيانات:": "Select Database:",
    "استدعاء الأمر التالي (السهم لأسفل)": "Next Command (Down Arrow)",
    "استدعاء الأمر السابق (السهم لأعلى)": "Prev Command (Up Arrow)",
    "استقبل إشعارات فورية على حسابك عند حدوث هجمات، توقف البوتات، أو ارتفاع استهلاك السيرفر.": "Receive instant Telegram notifications for attacks, bot crashes, or high loads.",
    "استهلاك الذاكرة الافتراضية Swap": "Swap Usage",
    "استهلاك الرام": "RAM Usage",
    "استهلاك المعالج": "CPU Usage",
    "استهلاك مساحة التخزين": "Disk Usage",
    "اسم البرنامج / الأمر": "Program / Command",
    "اسم النطاق (مثال: example.com)": "Domain Name",
    "الإجراءات": "Actions",
    "الانتقال لبداية السطر (Ctrl+A)": "Go to line start (Ctrl+A)",
    "الانتقال لنهاية السطر (Ctrl+E)": "Go to line end (Ctrl+E)",
    "البرامج والعمليات": "Processes",
    "القائمة": "Menu",
    "المجلد السابق": "Previous Folder",
    "المخزن المؤقت:": "Buffer:",
    "المسار / التوجيه": "Path / Route",
    "المسار: --": "Path: --",
    "المنافذ المفتوحة (Ports)": "Open Ports",
    "المهام المنجزة:": "Completed Tasks:",
    "النشطة حالياً:": "Currently Active:",
    "النطاق": "Domain",
    "النطاقات والشهادات": "Domains & SSL",
    "النوع": "Type",
    "بحث باسم البرنامج أو الـ PID...": "Search by Program or PID...",
    "بحث باسم الخدمة (مثل nginx, cron)...": "Search Service...",
    "بحث بالبورت أو اسم الخدمة...": "Search Port/Service...",
    "بحث بالـ IP أو المسار أو الأداة...": "Search IP/Path/Tool...",
    "بحث في المجلد الحالي...": "Search Current Folder...",
    "بروكسي (توجيه لمنفذ، مثل البوتات)": "Proxy (Route to port)",
    "تبديل المظهر (داكن/فاتح)": "Toggle Theme",
    "تحديث السجل": "Refresh Log",
    "تحديث السجلات": "Refresh Logs",
    "تحديث القائمة": "Refresh List",
    "تحديث تلقائي:": "Auto Refresh:",
    "تحديث حالة البوتات": "Refresh Bots Status",
    "تحريك المؤشر يميناً": "Move Cursor Right",
    "تسجيل الخروج": "Logout",
    "تسجيل الدخول للسيرفر": "Server Login",
    "تسجيل بوت أو تطبيق جديد": "Register New Bot/App",
    "تسجيل تطبيق أو بوت جديد": "Register New App/Bot",
    "تشغيل بنظام Webhook (الأسرع والأفضل)": "Run via Webhook (Fastest)",
    "تصفح وتحديد الملف": "Browse & Select File",
    "تعليق العملية بالخلفية (Ctrl+Z / SIGTSTP)": "Suspend (Ctrl+Z)",
    "تغيير الثيم": "Change Theme",
    "تغيير اللغة": "Change Language",
    "تغييرات غير محفوظة": "Unsaved Changes",
    "تفريغ سجلات الأمان": "Clear Security Logs",
    "تفريغ كاش الرام وتنظيف مخلفات النظام": "Clear RAM & System Junk",
    "تنظيف السيرفر": "Clean Server",
    "تنظيف كاش حزم التحديثات (APT Package Cache Clean)": "APT Package Cache Clean",
    "تنفيذ الأمر (Enter)": "Execute Command (Enter)",
    "جاري تحميل النطاقات...": "Loading domains...",
    "جاري فحص العمليات النشطة...": "Scanning active processes...",
    "جاري فحص المنافذ المفتوحة...": "Scanning open ports...",
    "جاري فحص ورصد البوتات والتطبيقات قيد التشغيل...": "Scanning running bots...",
    "حالة SSL": "SSL Status",
    "حالة جدار الحماية وسجون Fail2Ban في النظام (System Fail2Ban & UFW)": "System Firewall & Fail2Ban Status",
    "حظر يدوي (Manual)": "Manual Ban",
    "حظر يدوي بواسطة المسؤول": "Manual Ban by Admin",
    "حفظ (Ctrl+S)": "Save (Ctrl+S)",
    "حفظ النطاق": "Save Domain",
    "حفظ وتشغيل البوت": "Save & Run Bot",
    "خروج / EOF (Ctrl+D)": "Exit / EOF (Ctrl+D)",
    "درع الأمان & Fail2Ban": "Security Shield & Fail2Ban",
    "رابط التوجيه": "Route URL",
    "رابط الويبهوك (Webhook URL)": "Webhook URL",
    "سبب الحظر الأمني": "Ban Reason",
    "سجل الهجمات ومحاولات التخمين والاختراق اللحظي (Live Attack Logs)": "Live Attack & Brute Force Logs",
    "سجلات النواة (Kernel/Dmesg)": "Kernel Logs (Dmesg)",
    "شهادات تنتهي قريباً": "Expiring Certificates",
    "فخ مسارات حساسة (Honeypot)": "Honeypot Trap",
    "فرض الاتصال الآمن (Force HTTPS)": "Force HTTPS",
    "كل 10 ثوانٍ": "Every 10s",
    "كل 3 ثوانٍ": "Every 3s",
    "كل التهديدات": "All Threats",
    "كلمة المرور": "Password",
    "كلمة المرور الحالية": "Current Password",
    "لم يتم تنفيذ استعلام بعد": "No query executed yet",
    "مثال: /root/my_bot/main.py": "Ex: /root/my_bot/main.py",
    "مثال: 123456789": "Ex: 123456789",
    "مثال: 123456789:ABCdefGhIJKlmNoPQRstuVWXyz": "Ex: 123456789:ABC...",
    "مثال: 192.168.1.50": "Ex: 192.168.1.50",
    "مثال: PHP Webhook Bot": "Ex: PHP Webhook Bot",
    "مثال: Telegram Notify Bot": "Ex: Telegram Notify Bot",
    "مثال: نشاط مشبوه وفحص غير مصرح": "Ex: Suspicious activity",
    "مجلد العمل (Working Directory)": "Working Directory",
    "مجلد جديد": "New Folder",
    "محاولة فاشلة": "Failed Attempt",
    "مدة التشغيل:": "Uptime:",
    "مسار البيئة الافتراضية (Python Venv)": "Virtual Env (Venv) Path",
    "مسار الملفات (اختياري)": "Files Path (Optional)",
    "مسار ملف التشغيل (Script Path)": "Script Path",
    "مستعرض ومحرر قواعد بيانات SQLite (Database Studio)": "SQLite Database Studio",
    "مسح الشاشة (Ctrl+L)": "Clear Screen (Ctrl+L)",
    "مصدر السجل:": "Log Source:",
    "معالجة وتصحيح الكلمات العربية وربط الحروف": "Arabic Reshaping & Correction",
    "ملء الشاشة": "Fullscreen",
    "موقع ثابت / PHP (ملفات)": "Static / PHP Site",
    "نطاقات محمية (SSL)": "Secured Domains",
    "نوع النطاق": "Domain Type",
    "⚡ تسريع وتنظيف السيرفر": "⚡ Boost Server"
}

with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in manual_trans.items():
        f.write(f'window.ar_to_en["{k}"] = "{v}";\n')

print("Added", len(manual_trans), "translations")
