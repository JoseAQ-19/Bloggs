import urllib.request, json
req = urllib.request.Request('https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs?per_page=15')
req.add_header('Accept', 'application/vnd.github.v3+json')
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
for run in data['workflow_runs']:
    if 'Writer Funds' not in run['name']: continue
    if run['conclusion'] == 'success': continue
    run_id = run['id']
    name = run['name']
    print(f"RUN: {name} (ID: {run_id}) - {run['status']}/{run['conclusion']}")
    jobs_req = urllib.request.Request(f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/{run_id}/jobs')
    jobs_req.add_header('Accept', 'application/vnd.github.v3+json')
    jobs_resp = json.loads(urllib.request.urlopen(jobs_req).read())
    for job in jobs_resp['jobs']:
        if job['conclusion'] != 'success':
            for step in job['steps']:
                if step['conclusion'] == 'failure':
                    print(f"  FAILED STEP: {step['name']}")
                    log_url = f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{job['id']}/logs"
                    try:
                        log_req = urllib.request.Request(log_url)
                        log_req.add_header('Accept', 'application/vnd.github.v3+json')
                        log_data = urllib.request.urlopen(log_req).read().decode('utf-8')
                        print("  LOGS:")
                        print('\n'.join(log_data.splitlines()[-40:]))
                    except Exception as e:
                        print(f"  Failed to fetch logs: {e}")
