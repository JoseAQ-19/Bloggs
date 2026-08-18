import os
import urllib.request
import urllib.error

REPO = "JoseAQ-19/Bloggs"
TOKEN = os.environ.get("GITHUB_TOKEN")

job_ids = [
    ("93818232994", "funds_en_writer"),
    ("93814627788", "creators_es_writer"),
    ("93801667977", "ia_saas_es_writer"),
    ("93800547584", "biohacking_en_scout_commit"),
    ("93764135647", "tools_es_writer")
]

def get_job_log(job_id, name):
    url = f"https://api.github.com/repos/{REPO}/actions/jobs/{job_id}/logs"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Python-Actions-Analyzer"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            out_file = f"scratch/log_{name}_{job_id}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved log for {name} ({job_id}) -> {out_file} ({len(content)} bytes)")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for job {job_id}: {e.read().decode('utf-8', errors='replace')[:200]}")
    except Exception as e:
        print(f"Failed to fetch log for job {job_id}: {e}")

def main():
    for job_id, name in job_ids:
        get_job_log(job_id, name)

if __name__ == "__main__":
    main()
