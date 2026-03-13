import os
import glob

def search_files(directory, terms):
    found_files = {}
    for filepath in glob.iglob(os.path.join(directory, '**/*.md'), recursive=True):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for term in terms:
                    if term.lower() in content:
                        if term not in found_files:
                            found_files[term] = []
                        found_files[term].append(filepath)
        except Exception:
            pass
    return found_files

terms = ["Azken Portu", "Shamrock Shake", "Waco's Body Recomp", "Pura Estafa"]
results = search_files('content', terms)

for term, files in results.items():
    print(f"Term: {term}")
    for f in files:
        print(f"  {f}")
