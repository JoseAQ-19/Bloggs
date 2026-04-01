import os, urllib.request, json
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get('GITHUB_TOKEN')

if not token:
    print("NO TOKEN!")
    exit(1)

headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
for wf in ['writer-funds-es.yml', 'writer-funds-en.yml']:
    url = f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/workflows/{wf}/runs?status=failure&per_page=1'
    try:
        req = urllib.request.Request(url, headers=headers)
        res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        runs = res.get('workflow_runs', [])
        if not runs:
            print(f"No failed runs found for {wf}")
            continue
        run = runs[0]
        run_id = run['id']
        print(f"\n--- Failed run for {wf} (Run ID: {run_id}) ---")
        jobs_url = run['jobs_url']
        j_req = urllib.request.Request(jobs_url, headers=headers)
        jobs_res = json.loads(urllib.request.urlopen(j_req).read().decode('utf-8'))
        for job in jobs_res.get('jobs', []):
            if job['conclusion'] == 'failure':
                print(f"Job failed: {job['name']} (Job ID: {job['id']})")
                log_url = f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{job['id']}/logs"
                try:
                    log_req = urllib.request.Request(log_url, headers=headers)
                    log_data = urllib.request.urlopen(log_req).read().decode('utf-8')
                    # Save to file to get the full log
                    with open(f"log_{job['id']}.txt", "w", encoding="utf-8") as f:
                        f.write(log_data)
                    print(f"Log saved to log_{job['id']}.txt")
                    print("Log tail:")
                    print('\n'.join(log_data.splitlines()[-40:]))
                except Exception as e:
                    print(f"Failed to fetch logs: {e}")
    except Exception as e:
        print(f"Error fetching runs for {wf}: {e}")
