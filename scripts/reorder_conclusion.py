import os
import json

def reorder(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Exact strings to look for
    C_ES = "En conclusión, el rápido desarrollo de estas dinámicas subraya la necesidad vital de mantenerse documentado y adaptar las estrategias corporativas ante futuros escenarios del mercado."
    C_EN = "In conclusion, the rapid evolution of these dynamics highlights the vital need to stay informed and adapt corporate strategies for future market scenarios."

    conclusion = None
    if C_ES in content:
        conclusion = C_ES
    elif C_EN in content:
        conclusion = C_EN

    if not conclusion:
        return False # No conclusion injected or already cleaned

    # Remove the conclusion from its current place
    content = content.replace(C_ES, '')
    content = content.replace(C_EN, '')
    
    # Limpiamos saltos de línea sobrantes al final del archivo antes de buscar el slot
    content = content.rstrip()

    # Identificar el punto de inserción (antes del Disclaimer o de la Metodología)
    markers = [
        "## Metodología",
        "## Methodology",
        "## Fuentes",
        "## Sources",
        "*Descargo de responsabilidad",
        "*Disclaimer",
        "**Descargo",
        "**Disclaimer",
        "Descargo de responsabilidad:"
    ]

    insert_pos = len(content)
    for m in markers:
        idx = content.find(m)
        if idx != -1 and idx < insert_pos:
            insert_pos = idx

    # If we found a marker, insert before it
    if insert_pos < len(content):
        # Extract the parts
        part1 = content[:insert_pos].rstrip()
        part2 = content[insert_pos:]
        new_content = part1 + '\n\n' + conclusion + '\n\n' + part2 + '\n'
    else:
        new_content = content + '\n\n' + conclusion + '\n'

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    json_path = 'ALL_FAILED_ARTICLES.json'
    if not os.path.exists(json_path):
        print("Missing json")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    count = 0
    for a in articles:
        if reorder(a['file']):
            count += 1
            
    print(f"Reordered conclusion in {count} files.")

if __name__ == '__main__':
    main()
