import urllib.request, json, sys, os

try:
    run_id = sys.argv[1]
    req = urllib.request.Request(f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/{run_id}/jobs", headers={"User-Agent": "Python", "Accept": "application/vnd.github+json"})
    res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    for j in res.get("jobs", []):
        if j['conclusion'] == 'failure':
            print(f"Job failed: {j['name']} (ID: {j['id']})")
            # Fetch log for this job
            log_req = urllib.request.Request(f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{j['id']}/logs", headers={"User-Agent": "Python"})
            try:
                log_data = urllib.request.urlopen(log_req).read().decode('utf-8')
                with open('failed_log.txt', 'w', encoding='utf-8') as f:
                    f.write(log_data)
                print("Log written to failed_log.txt")
            except Exception as le:
                print(f"Failed to fetch logs: {le}")
except Exception as e:
    print(f"Error: {e}")
