translations = {
    "لم يتم إضافة أي نطاقات بعد. انقر على \"إضافة نطاق جديد\" للبدء.": "No domains added yet. Click \"Add New Domain\" to start.",
    "تعديل إعدادات النطاق": "Edit Domain Settings",
    "إضافة نطاق جديد": "Add New Domain",
    "منتهية": "Expired",
    "مفعل": "Enabled",
    "شهادة صالحة": "Valid Certificate",
    "محمي (SSL)": "Secured (SSL)",
    "المصدر: ": "Issuer: ",
    "تاريخ الانتهاء: ": "Expiry Date: ",
    "غير معروف": "Unknown",
    "غير محمي": "Unsecured",
    "بروكسي": "Proxy",
    "ثابت (Static)": "Static",
    "الإعدادات": "Settings",
    "تفعيل SSL": "Enable SSL",
    "تجديد SSL": "Renew SSL",
    "مسح": "Delete",
    "خطأ في الاتصال بالسيرفر": "Server connection error",
    "الرجاء إدخال اسم النطاق": "Please enter a domain name",
    "الرجاء إدخال مسار الملفات": "Please enter files path",
    "الرجاء إدخال رابط التوجيه": "Please enter target URL",
    "جاري الحفظ...": "Saving...",
    "تم إضافة النطاق بنجاح!": "Domain added successfully!",
    "تم تعديل النطاق بنجاح!": "Domain edited successfully!",
    "حدث خطأ غير متوقع.": "An unexpected error occurred.",
    "هل أنت متأكد من حذف النطاق ": "Are you sure you want to delete domain ",
    "؟\nسيتم حذف إعدادات Nginx ولن يمكن التراجع عن هذا الإجراء.": "?\nNginx config will be deleted. This cannot be undone.",
    "جاري الحذف...": "Deleting...",
    "تم حذف النطاق بنجاح.": "Domain deleted successfully.",
    "جاري تثبيت الشهادة... قد يستغرق الأمر دقيقة، الرجاء الانتظار": "Installing SSL... This may take a minute, please wait",
    "تم تفعيل شهادة SSL بنجاح!": "SSL certificate enabled successfully!",
    "خطأ: ": "Error: "
}

with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in translations.items():
        safe_k = k.replace('"', '\\"').replace('\n', '\\n')
        safe_v = v.replace('"', '\\"').replace('\n', '\\n')
        f.write(f'window.ar_to_en["{safe_k}"] = "{safe_v}";\n')
