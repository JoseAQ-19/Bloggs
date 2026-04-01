import urllib.request, json
req = urllib.request.Request('https://api.github.com/repos/JoseAQ-19/Bloggs/actions/jobs/67268809071')
req.add_header('Accept', 'application/vnd.github.v3+json')
data = json.loads(urllib.request.urlopen(req).read())
print('Job:', data['name'])
for step in data['steps']: 
    print(f"{step['name']}: {step['conclusion']}")
