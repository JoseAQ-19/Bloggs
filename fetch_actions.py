import os, urllib.request, json
token = os.environ.get('GITHUB_TOKEN')
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
                print(f"Log URL: {log_url}")
                try:
                    log_req = urllib.request.Request(log_url, headers=headers)
                    log_data = urllib.request.urlopen(log_req).read().decode('utf-8')
                    print("Log tail:")
                    print('\n'.join(log_data.splitlines()[-50:]))
                except Exception as e:
                    print(f"Failed to fetch logs: {e}")
    except Exception as e:
        print(f"Error fetching runs for {wf}: {e}")
