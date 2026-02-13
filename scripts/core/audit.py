import os
import frontmatter
from dotenv import load_dotenv

load_dotenv()
CONTENT_DIR = "content"
MIN_WORDS = 300
AI_PATTERNS = ["TL;DR", "Key Takeaways", "En resumen", "As an AI"]

def run_audit():
    print("🕵️‍♂️ [CLI] INICIANDO AUDITORÍA SEO...")
    total = 0
    passed = 0
    failed = 0
    
    for root, dirs, files in os.walk(CONTENT_DIR):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            total += 1
            filepath = os.path.join(root, filename)
            
            try:
                post = frontmatter.load(filepath)
                content = post.content.strip()
                words = len(content.split())
                
                issues = []
                if words < MIN_WORDS: issues.append(f"Thin ({words}w)")
                if not post.get('description'): issues.append("No Desc")
                
                if issues:
                    print(f"🔴 {filename[:40]}... -> {', '.join(issues)}")
                    failed += 1
                else:
                    passed += 1
            except:
                pass

    print(f"\n📊 RESUMEN: {total} Posts | ✅ {passed} OK | 🔴 {failed} Issues")
