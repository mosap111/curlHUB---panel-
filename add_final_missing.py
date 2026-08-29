translations = {
    " يوم": " days",
    " ساعة": " hours",
    " دقيقة": " minutes",
    "إنهاء (Kill)": "Kill",
    " بورت": " ports",
    " منفذ يستمع للطلبات": " listening ports",
    " معروض": " displayed",
    " خدمة": " services",
    " عملية": " processes",
    " نشطة تعمل الآن": " running now"
}
with open('static/i18n.js', 'a', encoding='utf-8') as f:
    for k, v in translations.items():
        f.write(f'window.ar_to_en["{k}"] = "{v}";\n')
