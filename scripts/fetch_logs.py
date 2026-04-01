import urllib.request, json, os
import zipfile, io

try:
    token = os.getenv('GITHUB_TOKEN', 'YOUR_TOKEN_HERE') # From env
    run_id = '23153782377'
    jobs_req = urllib.request.Request(f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/{run_id}/jobs')
    jobs_req.add_header('Authorization', f'Bearer {token}')
    jobs_req.add_header('Accept', 'application/vnd.github.v3+json')
    jobs_resp = json.loads(urllib.request.urlopen(jobs_req).read())
    
    for job in jobs_resp['jobs']:
        if job['conclusion'] != 'success':
            for step in job['steps']:
                if step['conclusion'] == 'failure':
                    print(f"FAILED STEP: {step['name']}")
            print(f"Job ID to get logs: {job['id']}")
            
            # Get logs for failed job
            log_req = urllib.request.Request(f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{job["id"]}/logs')
            log_req.add_header('Authorization', f'Bearer {token}')
            try:
                log_resp = urllib.request.urlopen(log_req)
                print(log_resp.read().decode('utf-8'))
            except Exception as e:
                print('Error reading text log:', e)
                
except Exception as e:
    print('Fatal Error:', e)
