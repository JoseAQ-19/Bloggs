import os
import json
import urllib.request
import urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "JoseAQ-19/Bloggs"

headers = {
    "Authorization": f"token {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Python-Workflow-Trigger"
}

def trigger_workflow(workflow_file, ref="main"):
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow_file}/dispatches"
    data = json.dumps({"ref": ref}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Triggered {workflow_file}: Status {response.status}")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} triggering {workflow_file}: {e.read().decode('utf-8')[:300]}")
        return False
    except Exception as e:
        print(f"Error triggering {workflow_file}: {e}")
        return False

if __name__ == "__main__":
    trigger_workflow("biohacking_en.yml")
