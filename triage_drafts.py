import os
import glob
import json
import audit_v2

def triage():
    draft_path = os.path.join(os.getcwd(), 'content', 'drafts_to_fix', '*.md')
    files = glob.glob(draft_path)
    
    results = []
    for f in files:
        if any(x in f for x in ['_index.md', 'about.md', 'contact.md', 'privacy.md', 'terms-of-service.md']):
            continue
        res = audit_v2.analyze_file(f)
        if res:
            # Calculate a composite rescue score (higher = easier to fix)
            composite = res.get('seo', 0) + res.get('eeat', 0) + res.get('geo', 0) + res.get('value', 0)
            issue_count = len(res.get('issues', []))
            results.append({
                'file': os.path.basename(f),
                'seo': res.get('seo', 0),
                'eeat': res.get('eeat', 0),
                'geo': res.get('geo', 0),
                'value': res.get('value', 0),
                'composite': composite,
                'issue_count': issue_count,
                'issues': res.get('issues', [])
            })
        else:
            # File passes audit! It's clean already.
            results.append({
                'file': os.path.basename(f),
                'seo': 10, 'eeat': 10, 'geo': 10, 'value': 10,
                'composite': 40,
                'issue_count': 0,
                'issues': ['CLEAN - Ready to publish']
            })
    
    # Sort: highest composite first (easiest to fix)
    results.sort(key=lambda x: (-x['composite'], x['issue_count']))
    
    # Stats
    clean = [r for r in results if r['issue_count'] == 0]
    easy = [r for r in results if 0 < r['issue_count'] <= 1 and r['composite'] >= 30]
    medium = [r for r in results if 1 < r['issue_count'] <= 2 and r['composite'] >= 20]
    hard = [r for r in results if r not in clean and r not in easy and r not in medium]

    report = []
    report.append("=" * 60)
    report.append("TRIAGE DE BORRADORES - CLASIFICACION POR RESCATABILIDAD")
    report.append("=" * 60)
    report.append(f"Total archivos analizados: {len(results)}")
    report.append(f"LIMPIOS (publicables ya):  {len(clean)}")
    report.append(f"FACILES (1 fix menor):     {len(easy)}")
    report.append(f"MEDIOS (2 fixes):          {len(medium)}")
    report.append(f"DIFICILES (3+ fixes):      {len(hard)}")
    report.append("=" * 60)

    report.append("\n--- TOP 15 MAS FACILES DE RESCATAR ---")
    for i, r in enumerate(results[:15], 1):
        report.append(f"\n{i}. {r['file']}")
        report.append(f"   Scores -> SEO:{r['seo']} EEAT:{r['eeat']} GEO:{r['geo']} Value:{r['value']} (Total:{r['composite']})")
        report.append(f"   Issues: {', '.join(r['issues'])}")
    
    report.append("\n\n--- BOTTOM 10 IRRECUPERABLES ---")
    for i, r in enumerate(results[-10:], 1):
        report.append(f"\n{i}. {r['file']}")
        report.append(f"   Scores -> SEO:{r['seo']} EEAT:{r['eeat']} GEO:{r['geo']} Value:{r['value']} (Total:{r['composite']})")
        report.append(f"   Issues: {', '.join(r['issues'])}")

    with open('triage_results.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # Also save full JSON for programmatic use
    with open('triage_full.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n'.join(report[:12]))
    print(f"\nResultados completos guardados en triage_results.txt y triage_full.json")

if __name__ == "__main__":
    triage()
