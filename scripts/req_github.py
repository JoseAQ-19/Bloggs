import urllib.request, json
import time

try:
    req = urllib.request.Request("https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs?per_page=15", headers={"User-Agent": "Python", "Accept": "application/vnd.github+json"})
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    with open('github_runs.txt', 'w', encoding='utf-8') as f:
        for r in res.get("workflow_runs", []):
            f.write(f"{r['name']} | {r['created_at']} | {r['conclusion']} | id: {r['id']}\n")
except Exception as e:
    with open('github_runs.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}")
