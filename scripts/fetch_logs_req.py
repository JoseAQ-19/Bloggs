import requests
import zipfile
import io
import os

token = os.getenv('GITHUB_TOKEN', 'YOUR_TOKEN_HERE')
run_id = '23153782377'

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get jobs
resp = requests.get(f'https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/{run_id}/jobs', headers=headers)
jobs_data = resp.json()

for job in jobs_data.get('jobs', []):
    if job['conclusion'] != 'success':
        print(f"FAILED JOB: {job['name']} (ID: {job['id']})")
        
        # Download logs
        log_url = f"https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/{job['id']}/logs"
        log_resp = requests.get(log_url, headers=headers)
        
        if log_resp.status_code == 200:
            print("LOGS FETCHED SUCCESSFULLY:")
            # Last 50 lines
            text = log_resp.text
            lines = text.splitlines()
            for line in lines[-50:]:
                print(line)
        else:
            print(f"Failed to fetch logs: {log_resp.status_code} - {log_resp.text}")
