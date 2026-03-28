import json
with open('results.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
for c in d['results']:
    print(f"Claim: {c['claim']['id']}")
    for s in c['sources']:
        print(f"  URL: {s['url']}")
        print(f"  Method: {s['fetch_method']}")
        print(f"  Lang: {s['language_detected']}")
        print(f"  Text Len: {len(s['article_text'])}")
        print('')
