import os
import json
import urllib.request
import urllib.error
import sys

# Force UTF-8 output encoding if possible
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = "JoseAQ-19/Bloggs"

headers = {
    "Authorization": f"token {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Python-Actions-Analyzer"
}

def api_get(url, use_auth=True):
    h = headers.copy() if (use_auth and TOKEN) else {"User-Agent": "Python-Actions-Analyzer"}
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 401 and use_auth:
            return api_get(url, use_auth=False)
        print(f"HTTP Error {e.code} for {url}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_job_logs(run_id, job_id):
    # Fetch job log if possible
    url = f"https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs"
    req = urllib.request.Request(url, headers={"User-Agent": "Python-Actions-Analyzer"})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"Could not fetch logs: {e}"

def main():
    print(f"=== ANALYZING GITHUB ACTIONS FOR {REPO} ===")
    runs_data = api_get(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=50")
    if not runs_data:
        print("Failed to fetch workflow runs.")
        return

    runs = runs_data.get("workflow_runs", [])
    print(f"Found {len(runs)} total workflow runs in response.\n")

    detailed_runs = []

    for r in runs:
        item = {
            "id": r["id"],
            "name": r["name"],
            "workflow_id": r["workflow_id"],
            "event": r["event"],
            "status": r["status"],
            "conclusion": r["conclusion"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "html_url": r["html_url"],
            "head_branch": r.get("head_branch"),
            "jobs": []
        }

        if r["conclusion"] == "failure":
            jobs_data = api_get(r["jobs_url"])
            if jobs_data:
                for j in jobs_data.get("jobs", []):
                    job_item = {
                        "id": j["id"],
                        "name": j["name"],
                        "status": j["status"],
                        "conclusion": j["conclusion"],
                        "started_at": j.get("started_at"),
                        "completed_at": j.get("completed_at"),
                        "failed_steps": []
                    }
                    if j.get("conclusion") == "failure":
                        for step in j.get("steps", []):
                            if step.get("conclusion") == "failure":
                                job_item["failed_steps"].append({
                                    "name": step.get("name"),
                                    "number": step.get("number"),
                                    "started_at": step.get("started_at"),
                                    "completed_at": step.get("completed_at")
                                })
                    item["jobs"].append(job_item)
        detailed_runs.append(item)

    with open("scratch/actions_report.json", "w", encoding="utf-8") as f:
        json.dump(detailed_runs, f, indent=2)

    failed_runs = [r for r in detailed_runs if r["conclusion"] == "failure"]
    success_runs = [r for r in detailed_runs if r["conclusion"] == "success"]

    print(f"Total Runs Analyzed: {len(detailed_runs)}")
    print(f"SUCCESS: {len(success_runs)}")
    print(f"FAILED: {len(failed_runs)}\n")

    print("=== DETAILS OF FAILED RUNS ===")
    for f in failed_runs:
        print(f"\nRun #{f['id']} - {f['name']}")
        print(f"  Created: {f['created_at']} | Event: {f['event']} | Branch: {f['head_branch']}")
        print(f"  URL: {f['html_url']}")
        for job in f["jobs"]:
            if job["conclusion"] == "failure":
                print(f"  - Job FAILED: {job['name']} (ID: {job['id']})")
                for step in job["failed_steps"]:
                    print(f"    * Step FAILED: Step {step['number']} - {step['name']}")

if __name__ == "__main__":
    main()
