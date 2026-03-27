import urllib.request, json, zipfile, io, re, os

token = os.getenv('GITHUB_TOKEN', 'YOUR_TOKEN_HERE')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json'
}

req = urllib.request.Request('https://api.github.com/repos/JoseAQ-19/Bloggs/actions/runs?per_page=15&status=success', headers=headers)
try:
    runs = json.loads(urllib.request.urlopen(req).read())['workflow_runs']
except Exception as e:
    open('scan_report.txt', 'w', encoding='utf-8').write(f"Error fetching runs: {e}")
    exit(1)

report = []
models_used = set()

for run in runs[:5]:
    report.append(f"Analizando Run: {run['name']} (ID: {run['id']})")
    try:
        log_url = run['logs_url']
        req_log = urllib.request.Request(log_url, headers=headers)
        resp = urllib.request.urlopen(req_log)
        
        with zipfile.ZipFile(io.BytesIO(resp.read())) as z:
            for logname in z.namelist():
                content = z.read(logname).decode('utf-8', errors='ignore')
                
                deepseek = len(re.findall(r'deepseek-chat', content, re.I))
                qwen = len(re.findall(r'qwen', content, re.I))
                llama = len(re.findall(r'llama-3', content, re.I))
                gemini = len(re.findall(r'gemini-2.0-flash', content, re.I))
                gpt4o = len(re.findall(r'gpt-4o', content, re.I))
                
                if deepseek > 0: models_used.add('DeepSeek V3 (OpenRouter/Groq)')
                if qwen > 0: models_used.add('Qwen (HuggingFace/Groq)')
                if llama > 0: models_used.add('Llama 3 (Groq)')
                if gemini > 0: models_used.add('Gemini 2.0 Flash (Fallback o Principal)')
                if gpt4o > 0: models_used.add('GPT-4o (GitHub/OpenAI)')
                
                t0 = len(re.findall(r'TIER 0', content))
                t1 = len(re.findall(r'TIER 1', content))
                t2 = len(re.findall(r'TIER 2', content))
                t3 = len(re.findall(r'TIER 3', content))
                t4 = len(re.findall(r'TIER 4', content))
                # Count explicitly when it falls back to Gemini!
                t_fall = len(re.findall(r'CASCADA ORIGINAL|Fallback', content, re.I))
                
                if any([t0, t1, t2, t3, t4, t_fall]):
                    report.append(f"  [{logname}] Tiers -> T0:{t0} T1:{t1} T2:{t2} T3:{t3} T4:{t4} Fallbacks:{t_fall}")

    except Exception as e:
        report.append(f"  Error extrayendo logs: {e}")

report.append("\\n--- APIs y Modelos Activamente Detectados en Logs ---")
for m in models_used: 
    report.append(f"- {m}")

with open('scan_report.txt', 'w', encoding='utf-8') as f:
    f.write("\\n".join(report))
