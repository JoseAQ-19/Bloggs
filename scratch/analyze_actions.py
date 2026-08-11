import os
import json
import urllib.request
import urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "JoseAQ-19/Bloggs"

headers = {
    "Authorization": f"token {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Python-Actions-Analyzer"
}

def api_get(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}: {e.read().decode('utf-8')[:300]}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    print(f"=== ANALYZING GITHUB ACTIONS FOR {REPO} ===")
    runs_data = api_get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=30")
    if not runs_data:
        print("Failed to fetch workflow runs.")
        return

    runs = runs_data.get("workflow_runs", [])
    print(f"Found {len(runs)} total workflow runs in response.\n")

    failed_runs = []
    success_runs = []
    other_runs = []

    for r in runs:
        item = {
            "id": r["id"],
            "name": r["name"],
            "workflow_id": r["workflow_id"],
            "event": r["event"],
            "status": r["status"],
            "conclusion": r["conclusion"],
            "created_at": r["created_at"],
            "html_url": r["html_url"],
            "head_branch": r.get("head_branch"),
            "jobs_url": r.get("jobs_url")
        }
        if r["conclusion"] == "failure":
            failed_runs.append(item)
        elif r["conclusion"] == "success":
            success_runs.append(item)
        else:
            other_runs.append(item)

    print(f"Summary: {len(failed_runs)} FAILED, {len(success_runs)} PASSED, {len(other_runs)} OTHER")

    print("\n--- FAILED WORKFLOW RUNS ---")
    for f in failed_runs:
        print(f"\n[Run #{f['id']}] {f['name']} | Event: {f['event']} | Branch: {f['head_branch']} | Created: {f['created_at']}")
        print(f"  URL: {f['html_url']}")
        
        # Fetch jobs for failed run
        jobs_data = api_get(f['jobs_url'])
        if jobs_data:
            for job in jobs_data.get("jobs", []):
                print(f"  Job: {job['name']} | Status: {job['status']} | Conclusion: {job['conclusion']}")
                for step in job.get("steps", []):
                    if step.get("conclusion") == "failure":
                        print(f"    ❌ Failed Step: {step['name']} (number: {step['number']})")
                        if "completed_at" in step:
                            print(f"       Completed at: {step['completed_at']}")

if __name__ == "__main__":
    main()
