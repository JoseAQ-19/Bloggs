import urllib.request, json
try:
    req = urllib.request.Request('https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs?per_page=15')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    
    for run in data['workflow_runs']:
        if 'Writer' not in run['name']: continue
        if run['conclusion'] == 'success': continue
        run_id = run['id']
        name = run['name']
        status = run['status']
        conclusion = run['conclusion']
        print(f"\\n--- RUN: {name} (ID: {run_id}) - {status}/{conclusion} ---")
        
        jobs_req = urllib.request.Request(f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/{run_id}/jobs')
        jobs_req.add_header('Accept', 'application/vnd.github.v3+json')
        jobs_resp = json.loads(urllib.request.urlopen(jobs_req).read())
        
        for job in jobs_resp['jobs']:
            if job['conclusion'] != 'success':
                for step in job['steps']:
                    if step['conclusion'] == 'failure':
                        print(f"FAILED STEP: {step['name']}")
                        # Fetch logs if it's the latest
                        log_url = f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{job['id']}"
                        print(f"Job Details: {log_url}")
                        
except Exception as e:
    print('Error:', e)
