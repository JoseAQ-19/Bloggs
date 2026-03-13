import subprocess

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode('utf-8')

try:
    branches = run_cmd('git branch -r').split('\n')
    for b in branches:
        b = b.strip()
        if '->' in b or not b:
            continue
        try:
            files = run_cmd(f'git ls-tree -r --name-only {b}')
            if 'azken' in files.lower() or 'shamrock' in files.lower() or 'waco' in files.lower():
                print(f"BRANCH: {b}")
                for line in files.split('\n'):
                    if any(term in line.lower() for term in ['azken', 'shamrock', 'waco']):
                        print(f"  {line}")
        except Exception as e:
            # print(f"Error checking {b}: {e}")
            pass
except Exception as e:
    print(f"Fatal error: {e}")
