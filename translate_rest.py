import re
import json

phrases = """الإجراء المتخذ
الإعدادات والتنبيهات
الاسم
الاسم الجديد:
الاسم:
البرامج والعمليات الأكثر استهلاكاً للموارد (Top Processes)
البرنامج والخدمة المستمعة
البروتوكول
البوتات المسجلة:
التاريخ والوقت
الحالة
الحجم
الحقول
الخيوط
الذاكرة (RAM)
الذاكرة العشوائية:
الذاكرة المحررة (RAM)
السجن المسؤول (Jail)
السطر: 1, العمود: 1
الشبكة:
الصادر:
الصلاحيات
الضغط:
الطرفية (Terminal)
العناوين المحظورة حالياً
الـ PID
الفرعية (Substate)
المتبقي:
المجلد الافتراضي:
المدة المتبقية
المسار المستهدف / التفاصيل
المستخدم
المستهلك الأكبر:
المعالج (CPU)
المعالج:
المنافذ المفتوحة والخدمات المستمعة (Listening Ports & Services)
المنفذ الافتراضي للوحة:
النتائج ستظهر هنا بعد تنفيذ الاستعلام أو النقر على أحد الجداول
النسخ الاحتياطي (Backups)
الوارد:
الوصف والدور
انتهت الجلسة، يرجى إعادة تسجيل الدخول
تأكيد
تأكيد كلمة المرور الجديدة
تاريخ الإنشاء
تاريخ التعديل
تاريخ ووقت الحظر
تحديث الآن
تحديث يدوي
تحريك المؤشر يساراً
تحميل الملف
تخمين تسجيل الدخول (Brute-Force)
تذكرني على هذا الجهاز
ترتيب حسب:
تشغيل بنظام Polling (في الخلفية)
تطبيق الحظر فوراً 🔒
تعديل الملف
تغيير كلمة المرور
تفريغ كاش الذاكرة والمخزن المؤقت (Drop Memory Caches)
تفعيل إرسال التنبيهات إلى تليجرام
تم إحباطها بنجاح
تم إعادة فحص قواعد البيانات
تم إيقاف التحديث التلقائي
تم الحذف بنجاح
تم تحديث السجل
تم تغيير كلمة المرور بنجاح!
تم تنفيذ مهام التحسين وتحرير الموارد بنجاح
تنبيهات وإشعارات تليجرام الفورية
تنظيف وضغط سجلات النظام القديمة (Systemd Journal Vacuum)
توكن البوت (Bot Token)
توكن بوت تليجرام (Bot Token)
جاري البحث عن قواعد البيانات...
جاري تحميل السجلات...
جاري تحميل النسخ الاحتياطية...
جاري جلب السجلات...
جاري جلب السطور...
جاري فحص خدمات النظام...
جاري فحص سجون Fail2Ban...
جلسة جديدة (Reset)
حالة الاتصال
حالة الخدمة
حالة الدرع:
حدث خطأ غير متوقع
حذف
حظر التخمين التلقائي:
حظر عنوان IP يدوياً
حفظ الإعدادات
حفظ الملف
حفظ كلمة المرور الجديدة
حفظ وتسجيل البوت
خدمات وتطبيقات السيرفر (System Services & Daemons)
خطأ في الاستعلام
دخول إلى اللوحة
درع الأمان والتحصين الشامل (Active Defense & Honeypots)
دعم اللغة العربية:
رفع ملفات
رقم العملية (PID)
رقم المنفذ (Port)
زر الهروب / الإلغاء (ESC)
ساعة واحدة
سجل مخرجات البوت (Console Output)
سجلات أخطاء Nginx (Errors)
سجلات أمان SSH
سجلات النظام (Logs)
سجلات حظر Fail2Ban
سجلات وصول Nginx (Access)
شغالة
عناوين IP المحظورة في سجون النظام (System Banned IPs):
عنوان الربط (Binding IP)
عنوان الـ IP
عنوان الـ IP المراد حظره
فحص القواعد
فشل رفع الملفات
فلترة وبحث في السطور...
قائمة عناوين الـ IP المحظورة حالياً (Active Banned IPs)
قم بتعيين كلمة مرور قوية لتأمين لوحة تحكم السيرفر والطرفية.
قواعد البيانات (SQLite)
كل 5 ثوانٍ
كلمة المرور الجديدة
لا توجد عناوين محظورة حالياً - النظام آمن 100% 🛡️
لا توجد هجمات مسجلة حتى الآن 🛡️
لم يتم فتح أي ملف
ماسحات ومصائد المسارات
متوسط الضغط:
مجموع التهديدات والماسحات المعترضة
محاولات تخمين الدخول
محرر الأكواد (Editor)
مدة الحظر
مدير البوتات (Bots)
مدير البوتات والتطبيقات الذكي (Bots & Python Apps Manager)
مدير الملفات (Files)
مدير النسخ الاحتياطي والاستعادة الفورية (Backups & Disaster Recovery)
مراقبة الأداء والمنافذ (Monitor)
مساحة القرص المستعادة
مسار الملف الأساسي للبوت
مستعرض سجلات النظام والخادم الموحد (Unified Log Explorer)
مسح السجلات
مسح الشاشة
مسح الملفات المؤقتة القديمة في /tmp
مصائد المسارات (Honeypots):
معرف المحادثة (Chat ID)
معلقة
معلومات السيرفر والبيئة
مفاتيح سريعة:
مفعل (5 محاولات = حظر 15 دقيقة) 🔒
ملف جديد
ملفات النسخ الاحتياطي المحفوظة
ممتاز، إغلاق
ممنوعون من الوصول مؤقتاً
نائمة
نتائج الاستعلام
نتيجة تنظيف وتسريع السيرفر
نسخ إعدادات وكود لوحة السيرفر
نسيت الكلمة؟
نشط ويعمل 100% 🛡️
نظام التشغيل:
نوع التهديد:
نوع الهجوم / التهديد
هجوم تم صده
هل تريد تفريغ وحذف سجلات الأمان والهجمات بالكامل؟
يرجى اختيار قاعدة بيانات أولاً
يرجى كتابة استعلام SQL
▲ السابق
▼ التالي
⚡ تجربة إرسال تنبيه
⚡ تنظيف وتسريع
⚡ تنفيذ (Run Query)
✨ تصحيح ودعم اللغة العربية (BiDi & Reshaping)
➕ إضافة تطبيق/بوت
➕ حظر IP يدوي
🌐 ويبهوك
🐍 بايثون (Python)
🐘 بي إتش بي (PHP)
📂 تصفح وتحديد الملف
📋 جداول القاعدة
📦 نسخ القواعد الآن
📦 نسخ اللوحة الآن
🔄 تحديث
🔍 ذكاء
🔍 فحص الملف""".split('\n')

manual_trans = {
    "الإجراء المتخذ": "Action Taken",
    "الإعدادات والتنبيهات": "Settings & Alerts",
    "الاسم": "Name",
    "الاسم الجديد:": "New Name:",
    "الاسم:": "Name:",
    "البرامج والعمليات الأكثر استهلاكاً للموارد (Top Processes)": "Top Resource Consuming Processes",
    "البرنامج والخدمة المستمعة": "Listening Service & Program",
    "البروتوكول": "Protocol",
    "البوتات المسجلة:": "Registered Bots:",
    "التاريخ والوقت": "Date & Time",
    "الحالة": "Status",
    "الحجم": "Size",
    "الحقول": "Fields",
    "الخيوط": "Threads",
    "الذاكرة (RAM)": "Memory (RAM)",
    "الذاكرة العشوائية:": "RAM:",
    "الذاكرة المحررة (RAM)": "Freed RAM",
    "السجن المسؤول (Jail)": "Jail Name",
    "السطر: 1, العمود: 1": "Ln: 1, Col: 1",
    "الشبكة:": "Network:",
    "الصادر:": "Outgoing:",
    "الصلاحيات": "Permissions",
    "الضغط:": "Load:",
    "الطرفية (Terminal)": "Terminal",
    "العناوين المحظورة حالياً": "Currently Banned IPs",
    "الـ PID": "PID",
    "الفرعية (Substate)": "Substate",
    "المتبقي:": "Remaining:",
    "المجلد الافتراضي:": "Default Folder:",
    "المدة المتبقية": "Remaining Time",
    "المسار المستهدف / التفاصيل": "Target Path / Details",
    "المستخدم": "User",
    "المستهلك الأكبر:": "Top Consumer:",
    "المعالج (CPU)": "Processor (CPU)",
    "المعالج:": "CPU:",
    "المنافذ المفتوحة والخدمات المستمعة (Listening Ports & Services)": "Listening Ports & Services",
    "المنفذ الافتراضي للوحة:": "Default Panel Port:",
    "النتائج ستظهر هنا بعد تنفيذ الاستعلام أو النقر على أحد الجداول": "Results will appear here after executing query",
    "النسخ الاحتياطي (Backups)": "Backups",
    "الوارد:": "Incoming:",
    "الوصف والدور": "Description & Role",
    "انتهت الجلسة، يرجى إعادة تسجيل الدخول": "Session expired, please login again",
    "تأكيد": "Confirm",
    "تأكيد كلمة المرور الجديدة": "Confirm New Password",
    "تاريخ الإنشاء": "Creation Date",
    "تاريخ التعديل": "Modified Date",
    "تاريخ ووقت الحظر": "Ban Date & Time",
    "تحديث الآن": "Update Now",
    "تحديث يدوي": "Manual Update",
    "تحريك المؤشر يساراً": "Move Cursor Left",
    "تحميل الملف": "Download File",
    "تخمين تسجيل الدخول (Brute-Force)": "Brute-Force Login",
    "تذكرني على هذا الجهاز": "Remember me on this device",
    "ترتيب حسب:": "Sort By:",
    "تشغيل بنظام Polling (في الخلفية)": "Run in Polling Mode (Background)",
    "تطبيق الحظر فوراً 🔒": "Apply Ban Immediately 🔒",
    "تعديل الملف": "Edit File",
    "تغيير كلمة المرور": "Change Password",
    "تفريغ كاش الذاكرة والمخزن المؤقت (Drop Memory Caches)": "Drop Memory Caches",
    "تفعيل إرسال التنبيهات إلى تليجرام": "Enable Telegram Alerts",
    "تم إحباطها بنجاح": "Successfully foiled",
    "تم إعادة فحص قواعد البيانات": "Databases rescanned",
    "تم إيقاف التحديث التلقائي": "Auto-refresh stopped",
    "تم الحذف بنجاح": "Deleted successfully",
    "تم تحديث السجل": "Log updated",
    "تم تغيير كلمة المرور بنجاح!": "Password changed successfully!",
    "تم تنفيذ مهام التحسين وتحرير الموارد بنجاح": "Optimization and resource freeing completed successfully",
    "تنبيهات وإشعارات تليجرام الفورية": "Instant Telegram Alerts",
    "تنظيف وضغط سجلات النظام القديمة (Systemd Journal Vacuum)": "Systemd Journal Vacuum",
    "توكن البوت (Bot Token)": "Bot Token",
    "توكن بوت تليجرام (Bot Token)": "Telegram Bot Token",
    "جاري البحث عن قواعد البيانات...": "Scanning for databases...",
    "جاري تحميل السجلات...": "Loading logs...",
    "جاري تحميل النسخ الاحتياطية...": "Loading backups...",
    "جاري جلب السجلات...": "Fetching logs...",
    "جاري جلب السطور...": "Fetching rows...",
    "جاري فحص خدمات النظام...": "Scanning system services...",
    "جاري فحص سجون Fail2Ban...": "Scanning Fail2Ban jails...",
    "جلسة جديدة (Reset)": "New Session (Reset)",
    "حالة الاتصال": "Connection Status",
    "حالة الخدمة": "Service Status",
    "حالة الدرع:": "Shield Status:",
    "حدث خطأ غير متوقع": "An unexpected error occurred",
    "حذف": "Delete",
    "حظر التخمين التلقائي:": "Auto Brute-Force Ban:",
    "حظر عنوان IP يدوياً": "Manual IP Ban",
    "حفظ الإعدادات": "Save Settings",
    "حفظ الملف": "Save File",
    "حفظ كلمة المرور الجديدة": "Save New Password",
    "حفظ وتسجيل البوت": "Save & Register Bot",
    "خدمات وتطبيقات السيرفر (System Services & Daemons)": "System Services & Daemons",
    "خطأ في الاستعلام": "Query Error",
    "دخول إلى اللوحة": "Login to Panel",
    "درع الأمان والتحصين الشامل (Active Defense & Honeypots)": "Active Defense & Honeypots",
    "دعم اللغة العربية:": "Arabic Support:",
    "رفع ملفات": "Upload Files",
    "رقم العملية (PID)": "Process ID (PID)",
    "رقم المنفذ (Port)": "Port Number",
    "زر الهروب / الإلغاء (ESC)": "Escape / Cancel (ESC)",
    "ساعة واحدة": "1 Hour",
    "سجل مخرجات البوت (Console Output)": "Bot Console Output",
    "سجلات أخطاء Nginx (Errors)": "Nginx Error Logs",
    "سجلات أمان SSH": "SSH Security Logs",
    "سجلات النظام (Logs)": "System Logs",
    "سجلات حظر Fail2Ban": "Fail2Ban Ban Logs",
    "سجلات وصول Nginx (Access)": "Nginx Access Logs",
    "شغالة": "Running",
    "عناوين IP المحظورة في سجون النظام (System Banned IPs):": "System Banned IPs:",
    "عنوان الربط (Binding IP)": "Binding IP",
    "عنوان الـ IP": "IP Address",
    "عنوان الـ IP المراد حظره": "IP Address to Ban",
    "فحص القواعد": "Scan Databases",
    "فشل رفع الملفات": "Failed to upload files",
    "فلترة وبحث في السطور...": "Filter and search rows...",
    "قائمة عناوين الـ IP المحظورة حالياً (Active Banned IPs)": "Active Banned IPs List",
    "قم بتعيين كلمة مرور قوية لتأمين لوحة تحكم السيرفر والطرفية.": "Set a strong password to secure panel and terminal.",
    "قواعد البيانات (SQLite)": "Databases (SQLite)",
    "كل 5 ثوانٍ": "Every 5s",
    "كلمة المرور الجديدة": "New Password",
    "لا توجد عناوين محظورة حالياً - النظام آمن 100% 🛡️": "No banned IPs currently - System is 100% secure 🛡️",
    "لا توجد هجمات مسجلة حتى الآن 🛡️": "No attacks recorded yet 🛡️",
    "لم يتم فتح أي ملف": "No file opened",
    "ماسحات ومصائد المسارات": "Path Scanners & Honeypots",
    "متوسط الضغط:": "Avg Load:",
    "مجموع التهديدات والماسحات المعترضة": "Total Blocked Threats & Scanners",
    "محاولات تخمين الدخول": "Brute Force Attempts",
    "محرر الأكواد (Editor)": "Code Editor",
    "مدة الحظر": "Ban Duration",
    "مدير البوتات (Bots)": "Bots Manager",
    "مدير البوتات والتطبيقات الذكي (Bots & Python Apps Manager)": "Smart Bots & Apps Manager",
    "مدير الملفات (Files)": "File Manager",
    "مدير النسخ الاحتياطي والاستعادة الفورية (Backups & Disaster Recovery)": "Backups & Recovery Manager",
    "مراقبة الأداء والمنافذ (Monitor)": "Monitor & Ports",
    "مساحة القرص المستعادة": "Recovered Disk Space",
    "مسار الملف الأساسي للبوت": "Bot Main Script Path",
    "مستعرض سجلات النظام والخادم الموحد (Unified Log Explorer)": "Unified Log Explorer",
    "مسح السجلات": "Clear Logs",
    "مسح الشاشة": "Clear Screen",
    "مسح الملفات المؤقتة القديمة في /tmp": "Clear old /tmp files",
    "مصائد المسارات (Honeypots):": "Honeypots:",
    "معرف المحادثة (Chat ID)": "Chat ID",
    "معلقة": "Pending",
    "معلومات السيرفر والبيئة": "Server Info & Environment",
    "مفاتيح سريعة:": "Hotkeys:",
    "مفعل (5 محاولات = حظر 15 دقيقة) 🔒": "Enabled (5 attempts = 15m ban) 🔒",
    "ملف جديد": "New File",
    "ملفات النسخ الاحتياطي المحفوظة": "Saved Backup Files",
    "ممتاز، إغلاق": "Great, Close",
    "ممنوعون من الوصول مؤقتاً": "Temporarily Denied Access",
    "نائمة": "Sleeping",
    "نتائج الاستعلام": "Query Results",
    "نتيجة تنظيف وتسريع السيرفر": "Server Clean & Boost Result",
    "نسخ إعدادات وكود لوحة السيرفر": "Backup Panel Code & Settings",
    "نسيت الكلمة؟": "Forgot Password?",
    "نشط ويعمل 100% 🛡️": "Active & Working 100% 🛡️",
    "نظام التشغيل:": "OS:",
    "نوع التهديد:": "Threat Type:",
    "نوع الهجوم / التهديد": "Attack / Threat Type",
    "هجوم تم صده": "Attack Blocked",
    "هل تريد تفريغ وحذف سجلات الأمان والهجمات بالكامل؟": "Do you want to clear and delete all security logs?",
    "يرجى اختيار قاعدة بيانات أولاً": "Please select a database first",
    "يرجى كتابة استعلام SQL": "Please write an SQL query",
    "▲ السابق": "▲ Prev",
    "▼ التالي": "▼ Next",
    "⚡ تجربة إرسال تنبيه": "⚡ Test Alert",
    "⚡ تنظيف وتسريع": "⚡ Clean & Boost",
    "⚡ تنفيذ (Run Query)": "⚡ Execute (Run Query)",
    "✨ تصحيح ودعم اللغة العربية (BiDi & Reshaping)": "✨ Arabic Support (BiDi & Reshaping)",
    "➕ إضافة تطبيق/بوت": "➕ Add App/Bot",
    "➕ حظر IP يدوي": "➕ Manual IP Ban",
    "🌐 ويبهوك": "🌐 Webhook",
    "🐍 بايثون (Python)": "🐍 Python",
    "🐘 بي إتش بي (PHP)": "🐘 PHP",
    "📂 تصفح وتحديد الملف": "📂 Browse File",
    "📋 جداول القاعدة": "📋 Tables",
    "📦 نسخ القواعد الآن": "📦 Backup DBs Now",
    "📦 نسخ اللوحة الآن": "📦 Backup Panel Now",
    "🔄 تحديث": "🔄 Refresh",
    "🔍 ذكاء": "🔍 Intel",
    "🔍 فحص الملف": "🔍 Inspect File"
}

with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in manual_trans.items():
        # Escape quotes in keys and values
        safe_k = k.replace('"', '\\"')
        safe_v = v.replace('"', '\\"')
        f.write(f'window.ar_to_en["{safe_k}"] = "{safe_v}";\n')

print("Added", len(manual_trans), "JS translations")
