
import os
import glob
import re
import frontmatter

def final_audit():
    with open('FINAL_AUDIT_REPORT.log', 'w', encoding='utf-8') as report:
        report.write("🚀 Iniciando Auditoría Técnica Final (Modo Google Reviewer)...\n")
        content_dir = 'content'
        files = glob.glob(f'{content_dir}/**/*.md', recursive=True)
    
    issues = []
    
    # AI Footprint Patterns
    ai_patterns = [
        r"(?i)en conclusión", r"(?i)en resumen", r"(?i)in conclusion", 
        r"(?i)in summary", r"(?i)stay tuned", r"(?i)\(tl;dr\)"
    ]
    
    # YMYL Niches
    finance_niches = ['crypto', 'funds', 'realestate', 'finance']
    health_niches = ['fitness', 'salud', 'health']
    
    # Footer Keywords (English)
    en_keywords = ["Methodology and Sources", "Editorial Disclosure", "Related Articles"]
    es_keywords = ["Metodología y Fuentes", "Aviso Editorial", "Artículos Relacionados"]

    for filepath in files:
        if os.path.basename(filepath).startswith('_index'):
            continue
            
        # Ignore legal pages for article-specific rules
        is_legal = "terms" in filepath.lower() or "terminos" in filepath.lower() or "privacy" in filepath.lower() or "privacidad" in filepath.lower() or "cookies" in filepath.lower()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            post = frontmatter.loads(content)
            body = post.content
            lang_path = "es" if "/es/" in filepath.replace("\\", "/") else "en"
            
            # 1. Language Integrity
            if lang_path == "en":
                # Check for Spanish keywords in EN body footer area
                body_suffix = body[-1000:].lower()
                for es_kw in es_keywords:
                    if es_kw.lower() in body_suffix:
                        issues.append(f"[LANG_ERROR] Spanish keyword '{es_kw}' found in English file: {filepath}")
            else:
                # Check for English keywords in ES body footer area
                body_suffix = body[-1000:].lower()
                for en_kw in en_keywords:
                    if en_kw.lower() in body_suffix:
                        issues.append(f"[LANG_ERROR] English keyword '{en_kw}' found in Spanish file: {filepath}")
            
            # 2. Empty Links
            if "](#)" in body:
                issues.append(f"[LINK_ERROR] Empty/Anchor link '#' found in: {filepath}")
                
            # 3. AI Footprints in last 500 chars (excluding footer)
            # Find the start of the footer to check just before it
            footer_start = -1
            for kw in en_keywords + es_keywords:
                idx = body.find(kw)
                if idx != -1:
                    if footer_start == -1 or idx < footer_start:
                        footer_start = idx
            
            pre_footer = body[:footer_start] if footer_start != -1 else body
            last_paragraphs = pre_footer.strip().split('\n\n')[-2:]
            for p in last_paragraphs:
                for pattern in ai_patterns:
                    if re.search(pattern, p):
                        issues.append(f"[AI_FOOTPRINT] AI pattern '{pattern}' found in closing paragraph of: {filepath}")

            # 4. YMYL Disclaimers
            if not is_legal:
                normalized_path = filepath.lower().replace("\\", "/")
                is_health = any(n in normalized_path for n in health_niches)
                is_finance = any(n in normalized_path for n in finance_niches)
                
                if is_health:
                    if lang_path == "es" and "consejo, diagnóstico o tratamiento médico" not in body.lower():
                        issues.append(f"[YMYL_ERROR] Missing Health Disclaimer in ES: {filepath}")
                    if lang_path == "en" and "medical advice, diagnosis, or treatment" not in body.lower():
                        issues.append(f"[YMYL_ERROR] Missing Health Disclaimer in EN: {filepath}")
                
                if is_finance:
                    if lang_path == "es" and "asesoramiento financiero" not in body.lower():
                        issues.append(f"[YMYL_ERROR] Missing Finance Disclaimer in ES: {filepath}")
                    if lang_path == "en" and "financial advice" not in body.lower():
                        issues.append(f"[YMYL_ERROR] Missing Finance Disclaimer in EN: {filepath}")

            # 5. Internal Links Integrity (Related Articles)
            # We look for links like [Title](/es/niche/slug/)
            internal_links = re.findall(r'\[.*?\]\((/.*?/)\)', body)
            for link in internal_links:
                # Basic check: does it look like a content link?
                if "/es/" in link or "/en/" in link:
                    # Skip if it's just a folder link (ending in /)
                    # /es/ or /es/fitness/
                    if link.count('/') <= 3:
                        continue
                        
                    # Convert URL to file path
                    # /es/fitness/slug/ -> content/es/fitness/slug.md
                    parts = link.strip('/').split('/')
                    if len(parts) >= 3:
                        target_path = os.path.join('content', *parts) + ".md"
                        if not os.path.exists(target_path):
                            # Try with _index.md
                            if not os.path.exists(os.path.join('content', *parts, "_index.md")):
                                issues.append(f"[404_LINK] Broken internal link '{link}' in: {filepath}")

        except Exception as e:
            issues.append(f"[SYSTEM_ERROR] Could not process {filepath}: {e}")

    # 6. Legal Pages Operational Check
    legal_required = ['content/es/terms-of-service.md', 'content/en/terms-of-service.md', 'content/es/privacy.md', 'content/en/privacy.md']
    for lp in legal_required:
        if not os.path.exists(lp):
            issues.append(f"[LEGAL_ERROR] Missing critical legal page: {lp}")

    # Report errors
    with open('FINAL_AUDIT_REPORT.log', 'a', encoding='utf-8') as f:
        if issues:
            f.write("\n🔴 NO-GO: Se han detectado errores críticos:\n")
            for err in issues:
                f.write(f"  {err}\n")
        else:
            f.write("\n🟢 GO DEFINITIVO: Todos los checkpoints de contenido han pasado.\n")

    return issues

if __name__ == "__main__":
    # Evitar emojis y acentos para compatibilidad con consolas Windows cp1252
    print("[AUDIT] Iniciando Auditoria Tecnica Final (Modo Google Reviewer)...")
    errors = final_audit()
    if errors:
        print("\n[NO-GO] Se han detectado errores criticos:")
        for err in errors:
            print(f"  {err}")
    else:
        print("\n[GO] Todos los checkpoints de contenido han pasado.")
