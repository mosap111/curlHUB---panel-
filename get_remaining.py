import re
from bs4 import BeautifulSoup
import json

html_phrases = set()

# Index.html
with open('static/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

arabic_pattern = re.compile(r'[\u0600-\u06FF]')

for text_node in soup.find_all(string=True):
    parent = text_node.parent
    if parent.name not in ['script', 'style']:
        text = text_node.strip()
        if arabic_pattern.search(text):
            html_phrases.add(text)

for element in soup.find_all(True):
    for attr in ['placeholder', 'title', 'value', 'data-tooltip']:
        if element.has_attr(attr):
            val = element[attr].strip()
            if arabic_pattern.search(val):
                html_phrases.add(val)

# JS files
for filename in ['static/app.v2.js', 'static/bots_advanced.js']:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find all strings
    matches = re.findall(r'["\'`]([^"\'`]+)["\'`]', content)
    for m in matches:
        if arabic_pattern.search(m):
            html_phrases.add(m)

# Current i18n
with open('static/i18n.js', 'r', encoding='utf-8') as f:
    i18n = f.read()

keys = set()
for line in i18n.split('\n'):
    if 'window.ar_to_en[' in line:
        try:
            k = line.split('window.ar_to_en["')[1].split('"] =')[0]
            k = k.replace('\\"', '"')
            keys.add(k)
        except:
            pass

missing = []
for p in html_phrases:
    if '${' in p:
        continue
    # Check if exact match exists
    if p not in keys:
        missing.append(p)

for m in sorted(missing):
    print(m)
