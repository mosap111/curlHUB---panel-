translations = {
    "جاري التحميل...": "Loading...",
    "حدث خطأ أثناء تحميل الملفات": "Error loading files",
    "إعادة تشغيل": "Restart",
    "حظر": "Ban",
    "الذاكرة الافتراضية (Swap)": "Virtual Memory (Swap)",
    "مساحة التخزين (Disk)": "Storage (Disk)"
}
with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in translations.items():
        f.write(f'window.ar_to_en["{k}"] = "{v}";\n')
