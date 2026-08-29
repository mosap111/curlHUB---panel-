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

# Now extract keys from i18n.js
with open('static/i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Crude extraction of dictionary keys
keys = []
for line in content.split('\n'):
    if ':' in line and '"' in line:
        try:
            key = line.split('":')[0].split('"')[-1]
            keys.append(key)
        except:
            pass

missing = html_phrases - set(keys)
for m in sorted(missing):
    print(m)
