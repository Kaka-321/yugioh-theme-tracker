import json
import os
import sys

# Add the crawler directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from themes import THEMES
from main import build_theme
from check_source import fetch_related_cards

# Test with blue-eyes theme
theme = THEMES[0]  # First theme (blue-eyes)
print(f"Testing theme: {theme.theme_id}")

try:
    # Test build_theme
    source = {
        "wikitext": "test wikitext",
        "title": "test",
        "url": "test",
    }
    result = build_theme(theme, source)
    print(f"Success: {result.get('canonical_name', 'N/A')}")
    
    # Test fetch_related_cards
    print(f"Testing fetch_related_cards...")
    related = fetch_related_cards(source)
    print(f"Found {len(related)} related cards")
    
    print("All tests passed!")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Test failed: {e}")