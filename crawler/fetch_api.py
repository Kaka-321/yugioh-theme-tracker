import urllib.request
import json
import re
import html

API_URL = 'https://yugipedia.com/api.php'
params = {
    'action': 'parse',
    'format': 'json',
    'formatversion': '2',
    'page': 'A.I.',
    'prop': 'wikitext|categories|extracts',
    'redirects': '1',
    'clprop': '|exif|thumb',
    'cllimit': '50'
}

query = '&'.join(f'{k}={v}' for k, v in params.items())
url = API_URL + '?' + query

req = urllib.request.Request(url, headers={
    'User-Agent': 'YugiohThemeTracker/0.1',
    'Accept': 'application/json'
})

with urllib.request.urlopen(req, timeout=30) as response:
    data = json.loads(response.read().decode('utf-8'))

parse = data.get('parse', {})

print('=== TITLE ===')
print(parse.get('title'))
print()

print('=== FULL URL ===')
print(parse.get('fullurl'))
print()

print('=== CATEGORIES ===')
categories = parse.get('categories', [])
print(f'  Total: {len(categories)}')
for i, cat in enumerate(categories):
    print(f'  [{i}] {json.dumps(cat, ensure_ascii=False, indent=2)}')
print()

print('=== EXTRACTS ===')
extracts = parse.get('extracts', [])
print(f'  Total: {len(extracts)}')
for i, ex in enumerate(extracts[:5]):
    print(f'  [{i}] {json.dumps(ex, ensure_ascii=False)}')
print()

print('=== WIKITEXT (first 2000 chars) ===')
wt = parse.get('wikitext', '')
print(wt[:2000])
print()

# Card names extraction from table
print('=== CARDS FROM TABLE ===')
# Find the table content between {| and |}
table_match = re.search(r'\{\|.*?\|\}', wt, re.DOTALL)
if table_match:
    table_content = table_match.group()
    print(f'  Table found, length: {len(table_content)}')
    
    # Simple pattern: extract card names from [[...]] links in table
    # Use a non-greedy pattern
    card_pattern = r'\[\[([^]|]+?)\]\]'
    card_links = re.findall(card_pattern, table_content)
    cards = []
    for link in card_links:
        if '|' not in link and not link.startswith(('Category:', 'File:', 'User:', 'Template:')):
            cards.append(link)
    print(f'  Cards found: {len(cards)}')
    for i, card in enumerate(cards):
        print(f'  [{i}] {card}')
else:
    print('  No table found')

# Also check the infobox for image info
print()
print('=== INFOBOX IMAGE ===')
infobox_match = re.search(r'\{\{Infobox\s+archseries.*?\}\}', wt, re.DOTALL)
if infobox_match:
    infobox_text = infobox_match.group()
    image_match = re.search(r'\|\s*image\s*=\s*\[?\[([^]|]+?)\]|([^[]+)', infobox_text)
    if image_match:
        image_url = image_match.group(1) or image_match.group(2)
        print(f'  Image filename: {image_url}')
    caption_match = re.search(r'\|\s*caption\s*=\s*(.*?)\|', infobox_text, re.DOTALL)
    if caption_match:
        print(f'  Caption: {caption_match.group(1)[:100]}')