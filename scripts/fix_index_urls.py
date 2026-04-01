
import os
import yaml
import re

CONTENT_DIR = "content"
LANGS = ["es", "en"]
CATEGORIES = ["fitness", "ia", "crypto", "youtube", "viral", "tools"]

def fix_frontmatter(filepath, lang, category):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"⚠️ No encontrado: {filepath}")
        return

    match = re.search(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if not match:
        print(f"❌ Sin frontmatter válido: {filepath}")
        return

    fm_text = match.group(1)
    body = match.group(2)
    
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        print(f"❌ Error YAML: {filepath}")
        return

    # 1. ELIMINAR URL FORZADA (La fuente del mal)
    if 'url' in fm:
        del fm['url']
        print(f"✅ Eliminada URL forzada en {lang}/{category}")

    # 2. Asegurar Translation Key
    if 'translationKey' not in fm:
        fm['translationKey'] = f"section-{category}"

    # 3. TRADUCIR (Básico) si es EN
    if lang == "en":
        # Diccionario de traducciones básicas
        TRANS = {
            "fitness": ("Biohacking & Fitness", "Sports science, longevity, and evidence-based protocols."),
            "ia": ("AI & SaaS", "Artificial Intelligence trends, SaaS reviews, and automation tools."),
            "crypto": ("Crypto & Web3", "Cryptocurrency analysis, blockchain trends, and market insights."),
            "youtube": ("Creator Economy", "Strategies for YouTubers, streamers, and content creators."),
            "viral": ("Viral Trends", "Analysis of viral phenomena and social media trends."),
            "tools": ("Tools & Reviews", "The best software tools and apps for productivity.")
        }
        
        if category in TRANS:
            fm['title'] = TRANS[category][0]
            fm['description'] = TRANS[category][1]
            print(f"🇺🇸 Traducido EN: {category}")

    # Guardar
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("---\n")
        yaml.dump(fm, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        f.write("---\n")
        f.write(body)

def main():
    print("🧹 INICIANDO LIMPIEZA DE URLs EN _INDEX.MD...")
    
    for cat in CATEGORIES:
        for lang in LANGS:
            path = os.path.join(CONTENT_DIR, lang, cat, "_index.md")
            fix_frontmatter(path, lang, cat)

    print("\n🎉 Limpieza completada.")

if __name__ == "__main__":
    main()
