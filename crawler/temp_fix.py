import json

with open('../data/themes/blue-eyes.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

d['canonical_name'] = ''
d['related_cards'] = [
    {'title': 'Blue-Eyes White Dragon', 'canonical_title': 'blue-eyes-white-dragon'},
    {'title': 'Rage with Eyes of Blue', 'canonical_title': 'rage-with-eyes-of-blue'},
]

with open('../data/themes/blue-eyes.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')

print("完了！blue-eyes.json を更新しました。")