import urllib.request
import json
import re
import html
from urllib.parse import quote

# Get image URLs from specific card pages
cards_to_check = ['A.I. Connect', 'A.I. Challenge You', 'A.I. Contact']

for card_name in cards_to_check:
    # URL encode the card name
    encoded_name = quote(card_name)
    
    # Get page info with image info
    url = f'https://yugipedia.com/api.php?action=query&format=json&cltitles={encoded_name}&clprop=extracts|imageinfo&prop=imageinfo&iiprop=url|thumburl|exturl&cllimit=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'test/1.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            query = data.get('query', {})
            cltitles = query.get('cltitles', [])
            print(f'=== {card_name} (encoded: {encoded_name}) ===')
            if cltitles:
                print(f'  Title: {cltitles[0].get("title", "")}')
                pageid = cltitles[0].get('pageid', '')
                print(f'  PageID: {pageid}')
                
                # Get image info
                imageinfo = query.get('imageinfo', [])
                if imageinfo:
                    for img in imageinfo:
                        print(f'  URL: {img.get("url", "")}')
                        print(f'  Thumb URL: {img.get("thumburl", "")}')
                        print(f'  Ext URL: {img.get("exturl", "")}')
                        print(f'  Size: {img.get("size", "")}')
                
                # Get extracts
                extracts = cltitles[0].get('extracts', [])
                if extracts:
                    for ex in extracts:
                        src = ex.get('source', '')
                        thumb = ex.get('thumb', '')
                        if src:
                            print(f'  Extract source: {src}')
                            if thumb:
                                print(f'  Extract thumb: {thumb}')
            else:
                print('  No results')
                # Try to get the actual error
                errors = data.get('error', {})
                print(f'  Error: {errors}')
            print()
    except Exception as e:
        print(f'  Error: {e}')