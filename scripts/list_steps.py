import urllib.request, json
req = urllib.request.Request('https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs/23153782377/jobs')
req.add_header('Accept', 'application/vnd.github.v3+json')
data = json.loads(urllib.request.urlopen(req).read())
for job in data['jobs']:
    print(f"Job: {job['name']}, ID: {job['id']}")
    for step in job['steps']:
        print(f"  {step['name']}: {step['conclusion']}")
