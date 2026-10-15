import urllib.request, json

# Get image URL from a specific card page
url = 'https://yugipedia.com/api.php?action=query&format=json&cltitles=A.I.%20Connect&clprop=extracts|imageinfo|exturl&prop=imageinfo&iiprop=url|exturl|size&iiurlwidth=300&cllimit=50'
req = urllib.request.Request(url, headers={'User-Agent': 'YugiohThemeTracker/0.1', 'Accept': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read())
    
query = data.get('query', {})
print('=== CLTITLES ===')
for ct in query.get('cltitles', []):
    print(f'  {ct.get("title", "")} pageid={ct.get("pageid", "")}')
    
print()
print('=== IMAGEINFO ===')
for img in query.get('imageinfo', []):
    print(f'  url={img.get("url", "")}')
    print(f'  exturl={img.get("exturl", "")}')
    print(f'  size={img.get("size", "")}')
    print(f'  thumburl={img.get("thumburl", "")}')
    print()

print('=== EXTRAILS ===')
for ct in query.get('cltitles', []):
    pageid = ct.get('pageid', '')
    if pageid:
        url2 = f'https://yugipedia.com/api.php?action=query&format=json&prop=extracts&exintro=true&exprops=image|size&cltitles=Page-{pageid}&cllimit=1'
        req2 = urllib.request.Request(url2, headers={'User-Agent': 'YugiohThemeTracker/0.1', 'Accept': 'application/json'})
        with urllib.request.urlopen(req2, timeout=30) as r2:
            data2 = json.loads(r2.read())
            extracts = data2.get('query', {}).get('cltitles', [{}])[0].get('extracts', [])
            if extracts:
                for ex in extracts:
                    print(f'  source={ex.get("source", "")}')
                    print(f'  thumburl={ex.get("thumb", "")}')
                    break