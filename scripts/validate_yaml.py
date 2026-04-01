#!/usr/bin/env python3
"""
Validador de Frontmatter YAML para todos los .md en content/
Detecta y corrige errores de sintaxis que rompen Hugo/Vercel.
"""
import os
import re
import sys
import yaml

CONTENT_DIR = "content"
ERRORS = []
FIXED = []

def validate_frontmatter(filepath):
    """Lee un archivo .md y valida su frontmatter YAML."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        ERRORS.append((filepath, f"Cannot read: {e}"))
        return

    # Buscar frontmatter entre --- ... ---
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        if content.strip().startswith('---'):
            ERRORS.append((filepath, "Frontmatter abierto pero nunca cerrado (falta --- final)"))
        else:
            ERRORS.append((filepath, "No tiene frontmatter"))
        return

    yaml_str = match.group(1)

    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            ERRORS.append((filepath, f"Frontmatter no es un dict, es {type(data).__name__}"))
            return
    except yaml.YAMLError as e:
        ERRORS.append((filepath, f"YAML inválido: {e}"))
        # Intentar auto-fix
        fixed = try_autofix(filepath, content, yaml_str)
        if fixed:
            FIXED.append(filepath)
        return

    # Validaciones de contenido
    if 'title' not in data or not data['title']:
        ERRORS.append((filepath, "Falta 'title' en frontmatter"))
    if 'date' not in data:
        ERRORS.append((filepath, "Falta 'date' en frontmatter"))
    if 'draft' not in data:
        pass  # No es crítico

def try_autofix(filepath, content, yaml_str):
    """Intenta corregir errores YAML comunes."""
    fixed_yaml = yaml_str

    # Fix 1: Comillas sin escapar en title/description
    # title: "Something with "quotes" inside"  → title: "Something with 'quotes' inside"
    lines = fixed_yaml.split('\n')
    new_lines = []
    for line in lines:
        # Detectar líneas con valores entre comillas dobles que tienen comillas internas
        m = re.match(r'^(\s*\w+:\s*)"(.+)"(\s*)$', line)
        if m:
            prefix = m.group(1)
            value = m.group(2)
            suffix = m.group(3)
            # Si hay comillas dobles internas sin escapar
            inner = value.replace('\\"', '__ESC__')
            if '"' in inner:
                value = inner.replace('"', "'").replace('__ESC__', '\\"')
                line = f'{prefix}"{value}"{suffix}'
        new_lines.append(line)
    fixed_yaml = '\n'.join(new_lines)

    # Fix 2: Valores sin comillas que tienen dos puntos (causan error de nested mapping)
    # title: Something: With Colons  → title: "Something: With Colons"
    fix_lines = []
    for line in fixed_yaml.split('\n'):
        m = re.match(r'^(\s*)(title|description|featured_image):\s+([^"\[{].+)$', line)
        if m:
            indent = m.group(1)
            key = m.group(2)
            value = m.group(3).strip()
            # Si el valor contiene : y no está entre comillas
            if ':' in value:
                value = value.replace('"', "'")
                line = f'{indent}{key}: "{value}"'
        fix_lines.append(line)
    fixed_yaml = '\n'.join(fix_lines)

    # Verificar si el fix funciona
    try:
        data = yaml.safe_load(fixed_yaml)
        if isinstance(data, dict):
            # Reconstruir el archivo
            rest_match = re.match(r'^---\s*\n.*?\n---(.*)$', content, re.DOTALL)
            rest = rest_match.group(1) if rest_match else ""
            new_content = f"---\n{fixed_yaml}\n---{rest}"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  🔧 AUTO-FIXED: {filepath}")
            return True
    except:
        pass

    return False

def main():
    print("🔍 VALIDADOR DE FRONTMATTER YAML")
    print("=" * 50)

    total = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in sorted(files):
            if not fname.endswith('.md'):
                continue
            filepath = os.path.join(root, fname)
            total += 1
            validate_frontmatter(filepath)

    print(f"\n📊 RESULTADOS:")
    print(f"   Total archivos: {total}")
    print(f"   Auto-corregidos: {len(FIXED)}")
    print(f"   Con errores: {len(ERRORS)}")

    if FIXED:
        print(f"\n🔧 ARCHIVOS CORREGIDOS:")
        for f in FIXED:
            print(f"   ✅ {f}")

    if ERRORS:
        print(f"\n🚨 ERRORES ENCONTRADOS:")
        for filepath, error in ERRORS:
            print(f"   ❌ {filepath}")
            print(f"      → {error}")
        sys.exit(1)
    else:
        print(f"\n✅ TODOS LOS ARCHIVOS VÁLIDOS. GREEN LIGHT!")

if __name__ == "__main__":
    main()
