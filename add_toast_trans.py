translations = {
    "حدث خطأ في الاتصال": "Connection error occurred",
    "حدث خطأ": "An error occurred",
    "فشل التثبيت": "Installation failed",
    "فشل الحذف": "Deletion failed",
    "فشل في الحفظ": "Save failed",
    "جاري الاتصال بـ Let's Encrypt لاستخراج شهادة النطاق ": "Contacting Let's Encrypt to issue SSL for ",
    "... الرجاء الانتظار": "... Please wait"
}
with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in translations.items():
        f.write(f'window.ar_to_en["{k}"] = "{v}";\n')
