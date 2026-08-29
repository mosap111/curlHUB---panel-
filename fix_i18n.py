import json
import re

with open('static/i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '${' in line:
        continue
    new_lines.append(line)

new_lines.extend([
    'window.ar_to_en[" شغال"] = " running";\n',
    'window.ar_to_en[" محظور"] = " banned";\n',
    'window.ar_to_en[" بورت"] = " port";\n',
    'window.ar_to_en[" منفذ يستمع للطلبات"] = " listening ports";\n',
    'window.ar_to_en[" نشطة تعمل الآن"] = " running now";\n',
    'window.ar_to_en[" عملية"] = " processes";\n',
    'window.ar_to_en[" حدث"] = " events";\n',
    'window.ar_to_en[" سجون نظام نشطة"] = " active system jails";\n',
    'window.ar_to_en[" سطر"] = " lines";\n',
    'window.ar_to_en[" بورت نشط"] = " active ports";\n',
    'window.ar_to_en[" خدمة"] = " services";\n',
    'window.ar_to_en[" معروض"] = " displayed";\n',
    'window.ar_to_en[" جدول"] = " tables";\n',
    'window.ar_to_en[" ملف نسخة"] = " backup files";\n',
    'window.ar_to_en["المسار: "] = "Path: ";\n',
    'window.ar_to_en["المصدر: "] = "Source: ";\n',
    'window.ar_to_en["الرام الحالية: "] = "RAM: ";\n',
    'window.ar_to_en[" | القرص: "] = " | Disk: ";\n',
    'window.ar_to_en["السطر: "] = "Ln: ";\n',
    'window.ar_to_en[", العمود: "] = ", Col: ";\n',
    'window.ar_to_en["تعذر تحميل بيانات الأمان: "] = "Failed to load security data: ";\n',
    'window.ar_to_en["تعذر جلب النسخ الاحتياطية: "] = "Failed to fetch backups: ";\n',
    'window.ar_to_en["تعذر جلب قائمة البوتات: "] = "Failed to fetch bots: ";\n',
    'window.ar_to_en["تعذر فحص قواعد البيانات: "] = "Failed to scan databases: ";\n',
    'window.ar_to_en["تعذر قراءة السجل: "] = "Failed to read log: ";\n',
    'window.ar_to_en["تعذر قراءة هيكل القاعدة: "] = "Failed to read database structure: ";\n',
    'window.ar_to_en["خطأ أثناء جلب السجلات: "] = "Error fetching logs: ";\n',
    'window.ar_to_en["سجل مخرجات: "] = "Output Log: ";\n',
    'window.ar_to_en["تم إنشاء المجلد "] = "Created folder ";\n',
    'window.ar_to_en["تم إنشاء الملف "] = "Created file ";\n',
    'window.ar_to_en["تم فتح "] = "Opened ";\n',
    'window.ar_to_en["تم تنظيف السيرفر بنجاح! تم تحرير "] = "Server cleaned successfully! Freed ";\n',
    'window.ar_to_en["MB من الرام"] = "MB of RAM";\n',
    'window.ar_to_en["جاري رفع "] = "Uploading ";\n',
    'window.ar_to_en[" ملف..."] = " files...";\n',
])

with open('static/i18n.js', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

