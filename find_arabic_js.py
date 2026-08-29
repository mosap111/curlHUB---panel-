import re
import json

arabic_pattern = re.compile(r'[\u0600-\u06FF]')
js_phrases = set()

# Read app.v2.js
with open('static/app.v2.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    # Find strings inside single or double quotes or backticks
    # Very crude regex to extract string literals
    matches = re.findall(r'["\'`]([^"\'`]+)["\'`]', line)
    for m in matches:
        if arabic_pattern.search(m):
            js_phrases.add(m)

# Read i18n.js
with open('static/i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

keys = []
for line in content.split('\n'):
    if ':' in line and '"' in line:
        try:
            key = line.split('":')[0].split('"')[-1]
            keys.append(key)
        except:
            pass
    if '=' in line and 'ar_to_en' in line:
        try:
            # window.ar_to_en["..."] = "..."
            key = line.split('"]')[0].split('["')[-1]
            keys.append(key)
        except:
            pass

missing = js_phrases - set(keys)
for m in sorted(missing):
    print(m)
