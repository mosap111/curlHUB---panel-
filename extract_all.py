import re
from bs4 import BeautifulSoup
import json

with open('static/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

arabic_pattern = re.compile(r'[\u0600-\u06FF]')
html_phrases = set()

for text_node in soup.find_all(string=True):
    parent = text_node.parent
    if parent.name not in ['script', 'style', 'title']:
        text = text_node.strip()
        if arabic_pattern.search(text):
            html_phrases.add(text)

for element in soup.find_all(True):
    for attr in ['placeholder', 'title', 'value', 'data-tooltip']:
        if element.has_attr(attr):
            val = element[attr].strip()
            if arabic_pattern.search(val):
                html_phrases.add(val)

# Extract from app.v2.js
with open('static/app.v2.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    matches = re.findall(r'["\'`]([^"\'`]+)["\'`]', line)
    for m in matches:
        if arabic_pattern.search(m):
            html_phrases.add(m)

# Now check i18n.js
with open('static/i18n.js', 'r', encoding='utf-8') as f:
    i18n_content = f.read()

keys = []
for line in i18n_content.split('\n'):
    if 'window.ar_to_en[' in line:
        try:
            # Match window.ar_to_en["KEY"]
            match = re.search(r'window\.ar_to_en\["([^"]+)"\]', line)
            if match:
                keys.append(match.group(1))
            else:
                # older format
                if ':' in line and '"' in line:
                    key = line.split('":')[0].split('"')[-1]
                    keys.append(key)
        except:
            pass

missing = html_phrases - set(keys)
for m in sorted(missing):
    print(m)
