#!/usr/bin/env python3
"""
🕵️ OPERACIÓN SHERLOCK: Auditoría Forense de Imágenes
Escanea todos los .md, verifica featured_image contra archivos reales.
"""
import os
import re
import yaml
from pathlib import Path

CONTENT_DIR = "content"
STATIC_DIR = "static"
MIN_IMAGE_SIZE = 100 * 1024  # 100KB - below this = likely placeholder/corrupt

def extract_frontmatter(filepath):
    """Extract YAML frontmatter from markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
    except Exception as e:
        return {"_error": str(e)}
    return {}

def audit():
    errors = []
    warnings = []
    ok_count = 0
    no_image_count = 0
    total = 0

    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in files:
            if not fname.endswith('.md') or fname == '_index.md':
                continue
            
            total += 1
            filepath = os.path.join(root, fname)
            fm = extract_frontmatter(filepath)
            
            if "_error" in fm:
                errors.append({
                    "post": filepath,
                    "title": fname,
                    "issue": f"YAML ROTO: {fm['_error']}",
                    "frontmatter_value": "N/A",
                    "file_exists": False,
                    "file_size": 0
                })
                continue
            
            featured = fm.get("featured_image", "")
            if not featured:
                no_image_count += 1
                continue
            
            # Check if external URL
            if featured.startswith("http"):
                errors.append({
                    "post": filepath,
                    "title": fm.get("title", fname)[:60],
                    "issue": "URL EXTERNA (debería ser local)",
                    "frontmatter_value": featured[:100],
                    "file_exists": False,
                    "file_size": 0
                })
                continue
            
            # Check local file
            # featured_image typically starts with /images/...
            # which maps to static/images/...
            local_path = os.path.join(STATIC_DIR, featured.lstrip("/"))
            exists = os.path.isfile(local_path)
            size = os.path.getsize(local_path) if exists else 0
            
            if not exists:
                errors.append({
                    "post": filepath,
                    "title": fm.get("title", fname)[:60],
                    "issue": "ARCHIVO NO EXISTE",
                    "frontmatter_value": featured,
                    "file_exists": False,
                    "file_size": 0
                })
            elif size < MIN_IMAGE_SIZE:
                warnings.append({
                    "post": filepath,
                    "title": fm.get("title", fname)[:60],
                    "issue": f"IMAGEN SOSPECHOSA ({size/1024:.0f}KB < 100KB)",
                    "frontmatter_value": featured,
                    "file_exists": True,
                    "file_size": size
                })
            else:
                ok_count += 1

    # === REPORT ===
    print("=" * 60)
    print("🕵️  OPERACIÓN SHERLOCK: INFORME FORENSE")
    print("=" * 60)
    print(f"\n📊 RESUMEN:")
    print(f"   Total posts escaneados: {total}")
    print(f"   ✅ Imagen OK:           {ok_count}")
    print(f"   ❌ ERRORES:             {len(errors)}")
    print(f"   ⚠️  SOSPECHOSOS:        {len(warnings)}")
    print(f"   🔲 Sin imagen:          {no_image_count}")
    
    if errors:
        print(f"\n{'=' * 60}")
        print(f"❌ ERRORES ({len(errors)}):")
        print(f"{'=' * 60}")
        for i, e in enumerate(errors):
            print(f"\n[ERROR {i+1}] Post: \"{e['title']}\"")
            print(f"   Archivo: {e['post']}")
            print(f"   - Frontmatter dice: \"{e['frontmatter_value']}\"")
            print(f"   - Problema: {e['issue']}")
            print(f"   - Archivo local: {'EXISTE' if e['file_exists'] else 'No existe'}")
            print("-" * 50)
    
    if warnings:
        print(f"\n{'=' * 60}")
        print(f"⚠️  SOSPECHOSOS ({len(warnings)}):")
        print(f"{'=' * 60}")
        for i, w in enumerate(warnings):
            print(f"\n[WARN {i+1}] Post: \"{w['title']}\"")
            print(f"   Archivo: {w['post']}")
            print(f"   - Frontmatter dice: \"{w['frontmatter_value']}\"")
            print(f"   - Archivo local: EXISTE (Pero pesa {w['file_size']/1024:.0f}KB -> SOSPECHOSO)")
            print("-" * 50)
    
    # === CATEGORIZED SUMMARY ===
    if errors:
        ext_urls = [e for e in errors if "EXTERNA" in e['issue']]
        missing = [e for e in errors if "NO EXISTE" in e['issue']]
        yaml_broken = [e for e in errors if "YAML" in e['issue']]
        
        print(f"\n{'=' * 60}")
        print("📋 DESGLOSE POR TIPO DE ERROR:")
        print(f"{'=' * 60}")
        if ext_urls:
            print(f"   🌐 URLs externas (Pollinations/etc): {len(ext_urls)}")
        if missing:
            print(f"   🚫 Archivo local no existe:           {len(missing)}")
        if yaml_broken:
            print(f"   💥 YAML roto:                         {len(yaml_broken)}")
        if warnings:
            print(f"   📏 Imagen < 100KB (placeholder?):     {len(warnings)}")

    if not errors and not warnings:
        print("\n🎉 ¡PERFECTO! Todas las imágenes están OK.")

if __name__ == "__main__":
    audit()
