import re
import json

phrases = """0 بورت
0 شغال
0 عملية
0 محظور
0 منفذ نشط
15 دقيقة
2 GB RAM + 3 GB Swap (مفعلة)
21 مسار فخ نشط 🪤
24 ساعة (يوم كامل)
30 دقيقة
5 سجون نشطة
IP محظور
curlHUB - لوحة تحكم السيرفر
أداة / متصفح المهاجم
أداة مصطادة
أدوات الويبهوك לבوتات PHP
أدوات فحص وتخمين مسارات (Scanners)
أسبوع كامل
أفلت الملفات هنا لرفعها فوراً
أوامر سريعة:
إجراء
إجراء فك الحظر
إجراءات التحكم
إشعار عند تعطل أو توقف أي بوت
إشعار عند حظر هجوم أو ماسح أمني جديد
إعادة الاتصال
إعادة تشغيل الخدمة
إغلاق
إكمال تلقائي للأوامر والمسارات (TAB)
إلغاء
إنشاء جديد
اختر قاعدة بيانات من القائمة أعلاه
استعلام SQL:
استهلاك الرام الإجمالي:
اسم البوت
اسم البوت / التطبيق
اسم الخدمة (Service Unit)
اسم المستخدم
اسم الملف
الأعلى ذاكرة (RAM)
الأعلى معالجاً (CPU)""".split('\n')

translations = {
    "0 بورت": "0 ports",
    "0 شغال": "0 running",
    "0 عملية": "0 processes",
    "0 محظور": "0 banned",
    "0 منفذ نشط": "0 active ports",
    "15 دقيقة": "15 minutes",
    "2 GB RAM + 3 GB Swap (مفعلة)": "2 GB RAM + 3 Swap (Enabled)",
    "21 مسار فخ نشط 🪤": "21 active honeypot paths 🪤",
    "24 ساعة (يوم كامل)": "24 hours (1 day)",
    "30 دقيقة": "30 minutes",
    "5 سجون نشطة": "5 active jails",
    "IP محظور": "Banned IP",
    "curlHUB - لوحة تحكم السيرفر": "curlHUB - Server Control Panel",
    "أداة / متصفح المهاجم": "Attacker Tool / Browser",
    "أداة مصطادة": "Caught Tool",
    "أدوات الويبهوك לבوتات PHP": "Webhook Tools for PHP Bots",
    "أدوات فحص وتخمين مسارات (Scanners)": "Path Scanners & Bruteforce",
    "أسبوع كامل": "1 week",
    "أفلت الملفات هنا لرفعها فوراً": "Drop files here to upload",
    "أوامر سريعة:": "Quick Commands:",
    "إجراء": "Action",
    "إجراء فك الحظر": "Unban Action",
    "إجراءات التحكم": "Control Actions",
    "إشعار عند تعطل أو توقف أي بوت": "Alert on bot crash or stop",
    "إشعار عند حظر هجوم أو ماسح أمني جديد": "Alert on new attack or scanner ban",
    "إعادة الاتصال": "Reconnect",
    "إعادة تشغيل الخدمة": "Restart Service",
    "إغلاق": "Close",
    "إكمال تلقائي للأوامر والمسارات (TAB)": "Auto-complete commands & paths (TAB)",
    "إلغاء": "Cancel",
    "إنشاء جديد": "Create New",
    "اختر قاعدة بيانات من القائمة أعلاه": "Select a database from the list above",
    "استعلام SQL:": "SQL Query:",
    "استهلاك الرام الإجمالي:": "Total RAM Usage:",
    "اسم البوت": "Bot Name",
    "اسم البوت / التطبيق": "Bot / App Name",
    "اسم الخدمة (Service Unit)": "Service Unit Name",
    "اسم المستخدم": "Username",
    "اسم الملف": "File Name",
    "الأعلى ذاكرة (RAM)": "Highest RAM",
    "الأعلى معالجاً (CPU)": "Highest CPU"
}

with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in translations.items():
        if k.strip():
            safe_k = k.replace('"', '\\"')
            safe_v = v.replace('"', '\\"')
            f.write(f'window.ar_to_en["{safe_k}"] = "{safe_v}";\n')

print("Added more JS translations")
