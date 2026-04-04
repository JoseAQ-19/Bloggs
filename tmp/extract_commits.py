import json
with open('tmp/events.json', 'r', encoding='utf-8-sig') as f:
    events_payload = json.load(f)
events = events_payload.get('value', []) if isinstance(events_payload, dict) else events_payload
for ev in events:
    if ev.get('type') == 'PushEvent':
        commits = ev.get('payload', {}).get('commits', [])
        for c in commits:
            print(f"{c['sha']} - {c['message'].splitlines()[0]}")
