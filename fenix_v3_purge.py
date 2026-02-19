#!/usr/bin/env python3
"""
FENIX V3 PURGE SCRIPT
Ejecuta la Fase 1 de la resurrección SEO:
- Cuarentena de artículos canibalizados (draft: true)
- Borrado de huellas Pollinations.ai
- Limpieza de meta descriptions genéricas
"""
import os
import re

CONTENT_DIR = "content"

# ============================================================
# CLUSTER MAP: Artículos a mantener (SURVIVORS) por cluster.
# Todo lo demás en el cluster se pasa a draft: true.
# ============================================================

# --- CLUSTER METAVERSO ES (mantener 1, purgar 6+) ---
SURVIVORS_ES_METAVERSO = {
    "content/es/ia/metaverso-muerte-hype.md",  # El más estructurado y completo
}
PURGE_ES_METAVERSO = {
    "content/es/ia/el-metaverso-esta-muerto-y-nadie-se-atreve-a-decir.md",
    "content/es/ia/el-metaverso-ha-muerto-ahora-toca-reirnos.md",
    "content/es/ia/el-metaverso-ha-muerto-bienvenidos-al-infierno-dig.md",
    "content/es/ia/el-metaverso-ha-muerto-larga-vida-al-caos-digital.md",
    "content/es/ia/el-metaverso-ha-muerto-quien-se-queda-con-los-hues.md",
    "content/es/ia/metaverso-el-gran-bluf-tecnologico-del-siglo-xxi.md",
    "content/es/ia/metaverso-zombie-vr-cripto-apocalipsis.md",
    "content/es/crypto/metaverso-estafa-piramidal-evitar.md",  # Cross-silo duplicate
}

# --- CLUSTER METAVERSO EN (mantener 1, purgar resto) ---
SURVIVORS_EN_METAVERSO = {
    "content/en/ia/metaverse-zucks-40-billion-mistake-en.md",
}
PURGE_EN_METAVERSO = {
    "content/en/ia/metaverse-pyramid-scheme-en.md",
    "content/en/ia/el-ano-en-que-la-realidad-virtual-derroto-al-mund.md",
    "content/en/crypto/metaverse-meltdown-crypto-vr-failure-en.md",
}

# --- CLUSTER SILICON VALLEY ES (mantener 1, purgar 3) ---
SURVIVORS_ES_SILICON = {
    "content/es/ia/silicon-valley-la-burbuja-que-nunca-exploto-pero-d.md",  # Más completo con data SVB
}
PURGE_ES_SILICON = {
    "content/es/ia/silicon-valley-esta-muerto-el-futuro-es-descentral.md",
    "content/es/ia/silicon-valley-la-burbuja-de-humo-que-engano-al-mu.md",
    "content/es/ia/silicon-valley-se-desangra-la-era-dorada-ha-termin.md",
}

# --- CLUSTER BITCOIN ES (mantener 1, purgar 7) ---
SURVIVORS_ES_BITCOIN = {
    "content/es/crypto/bitcoin-la-estafa-del-siglo-xxi-al-descubierto.md",  # Más completo, mejor datos
}
PURGE_ES_BITCOIN = {
    "content/es/crypto/bitcoin-la-burbuja-dorada-que-nunca-fue-oro.md",
    "content/es/crypto/bitcoin-la-burbuja-eterna-sostenida-por-el-hype.md",
    "content/es/crypto/bitcoin-la-fiebre-del-oro-digital-es-una-estafa-pi.md",
    "content/es/crypto/bitcoin-el-despertar-brutal-de-la-estafa-digital.md",
    "content/es/crypto/bitcoin-en-caida-libre-el-fin-de-la-era-dorada.md",
    "content/es/crypto/bitcoin-se-derrumba-la-borrachera-cripto-llega-a-s.md",
    "content/es/crypto/bitcoin-al-matadero-por-que-las-criptomonedas-sera.md",
}

# --- CLUSTER BITCOIN EN (mantener 1) ---
SURVIVORS_EN_BITCOIN = {
    "content/en/crypto/bitcoin-ha-muerto-y-esta-vez-es-para-siempre-autop.md",
}
# No hay más duplicados EN de Bitcoin

# --- CLUSTER GEOPOLITICA ES (mantener 1, purgar 2) ---
SURVIVORS_ES_GEO = {
    "content/es/ia/geopolitica-en-llamas-las-10-tendencias-que-incend.md",  # El más completo (listicle)
}
PURGE_ES_GEO = {
    "content/es/ia/geopolitica-2026-el-ano-en-que-la-realidad-supero.md",
    "content/es/ia/geopolitica-2026-el-ano-que-el-mundo-se-rompio-y-n.md",
}

# --- CLUSTER "SUEÑAN LOS ANDROIDES" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_ANDROIDES = {
    "content/es/ia/suenan-los-androides-con-ovejas-electricas-y-tu-co.md",
}
PURGE_ES_ANDROIDES = {
    "content/es/ia/suenan-los-borregos-con-ciber-ovejas-el-futuro-no.md",
}

# --- CLUSTER "AÑO QUE SE ROMPIÓ" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_ANO = {
    "content/es/ia/el-ano-en-que-el-futuro-se-rompio-y-nadie-hizo-na.md",
}
PURGE_ES_ANO = {
    "content/es/ia/el-ano-que-el-mundo-se-cayo-a-pedazos.md",
}

# --- CLUSTER ESPIONAJE/MOVIL ES (mantener 1, purgar 1) ---
SURVIVORS_ES_ESPIA = {
    "content/es/ia/tu-nevera-te-espia-el-futuro-orwelliano-que-ya-pag.md",
}
PURGE_ES_ESPIA = {
    "content/es/ia/celular-te-espia-y-le-pagas-por-ello.md",
    "content/es/ia/movil-te-traiciona-el-negocio-redondo-del-espionaj.md",
}

# --- CLUSTER "IA ESTAFA" ES (mantener 1, purgar 2) ---
SURVIVORS_ES_IA_ESTAFA = {
    "content/es/ia/inteligencia-artificial-la-estafa-del-siglo-xxi.md",
}
PURGE_ES_IA_ESTAFA = {
    "content/es/ia/ia-el-nuevo-mesias-que-te-dejara-en-la-calle.md",
    "content/es/ia/la-ia-no-viene-a-salvarnos-viene-a-explotarnos.md",
}

# --- CLUSTER "TABU DIGITAL" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_TABU = {
    "content/es/ia/el-tabu-tecnologico-lo-que-no-quieren-que-sepas.md",
}
PURGE_ES_TABU = {
    "content/es/ia/el-tabu-digital-por-que-nadie-se-atreve-a-decir-la.md",
}

# --- CLUSTER "CAPITALISMO/SISTEMA" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_CAPITALISMO = {
    "content/es/ia/el-capitalismo-zombi-anatomia-de-un-sistema-fallid.md",
}
PURGE_ES_CAPITALISMO = {
    "content/es/ia/el-capitalismo-zombi-como-la-codicia-corporativa-e.md",
}

# --- CLUSTER "NEUTRALIDAD/DATOS" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_NEUTRAL = {
    "content/es/ia/neutralidad-cero-la-gran-estafa-de-la-informacion.md",
}
PURGE_ES_NEUTRAL = {
    "content/es/ia/el-algoritmo-te-vigila-como-la-objetividad-de-los.md",
}

# --- CLUSTER "MITO PROGRESO/MESIAS" ES (mantener 1, purgar 1) ---
SURVIVORS_ES_MITO = {
    "content/es/ia/el-mito-del-progreso-como-la-ia-nos-vende-un-futur.md",
}
PURGE_ES_MITO = {
    "content/es/ia/el-mito-del-mesias-digital-como-silicon-valley-te.md",
}

# --- CLUSTER NOVUMWORLD META ES (mantener 0 - self-referential junk) ---
PURGE_ES_NOVUM = {
    "content/es/ia/novumworld-la-farsa-del-periodismo-de-elite-y-por.md",
    "content/es/ia/novumworld-la-burbuja-de-la-elite-que-nadie-quiere.md",
}

# --- CLUSTER FITNESS duplicados (mantener 1 ES + 1 EN, purgar copias) ---
SURVIVORS_ES_FITNESS = {
    "content/es/fitness/kinesiologia-ciencias-salud-alma-college-hipertrofia-longevidad.md",
}
PURGE_ES_FITNESS = {
    "content/es/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alm.md",
    "content/es/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alma-college.md",
}
SURVIVORS_EN_FITNESS = {
    "content/en/fitness/alma-college-kinesiology-hypertrophy-longevity-en.md",
}
PURGE_EN_FITNESS = {
    "content/en/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alm-en.md",
    "content/en/fitness/kinesiology-and-health-sciences-program-preparing-students-for-dynamic-careers-in-human-movement-alma-college-en.md",
}

# --- CLUSTER LAYERZERO EN (mantener 1, purgar 1) ---
SURVIVORS_EN_LAYERZERO = {
    "content/en/crypto/layerzero-trending-zero-blockchain-institutional-interest-market-dynamics-en.md",
}
PURGE_EN_LAYERZERO = {
    "content/en/crypto/why-is-layerzero-trending-today-in-crypto.md",
}

# --- CLUSTER EN - Artículos con título en español en silo inglés ---
PURGE_EN_WRONG_LANG = {
    "content/en/ia/el-futuro-no-te-gustara-verdades-incomodas-de-2026.md",
    "content/en/ia/la-ia-viene-a-quitarte-el-almuerzo-y-no-se-disculp.md",
    "content/en/ia/el-futuro-es-ahora-las-7-tendencias-que-los-gobier.md",
    "content/en/ia/la-ia-te-miente-por-que-la-personalidad-artificial.md",
    "content/en/ia/donde-estan-mis-coches-voladores-la-estafa-futuris.md",
    "content/en/crypto/bitcoin-ha-muerto-y-esta-vez-es-para-siempre-autop.md",
}

# --- CLUSTER NBA/YouTube (mantener 1 ES, purgar duplicate) ---
SURVIVORS_ES_NBA = {
    "content/es/youtube/nba-all-star-2026-estrategia-digital.md",
}
PURGE_ES_NBA = {
    "content/es/youtube/nba-gathers-200-plus-creators-for-all-star-weekend-in-los-angeles-variety.md",
}

# --- ES Crypto con títulos en inglés ---
PURGE_ES_WRONG_LANG = {
    "content/es/crypto/why-is-venice-token-trending-today-in-crypto.md",
    "content/es/crypto/why-is-berachain-trending-today-in-crypto.md",
}

# ============================================================
# CONSOLIDATE ALL PURGE TARGETS
# ============================================================
ALL_PURGE = set()
for var_name, var_val in list(locals().items()):
    if var_name.startswith("PURGE_"):
        ALL_PURGE.update(var_val)

# ============================================================
# GENERIC DESCRIPTION to remove
# ============================================================
GENERIC_DESC = "Análisis profundo sobre tecnología y tendencias digitales en NovumWorld."

# ============================================================
# EXECUTION
# ============================================================

def inject_draft(filepath):
    """Set draft: true in frontmatter."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace draft: false with draft: true
    if 'draft: false' in content:
        content = content.replace('draft: false', 'draft: true', 1)
    elif 'draft:' not in content:
        # Add draft: true after the first ---
        content = content.replace('---\n', '---\ndraft: true\n', 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def remove_pollinations_image(filepath):
    """Remove image: lines pointing to pollinations.ai."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = False
    for line in lines:
        if line.strip().startswith('image:') and 'pollinations.ai' in line:
            removed = True
            continue
        new_lines.append(line)
    
    if removed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return removed

def fix_generic_description(filepath):
    """Remove generic description or replace with empty."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if GENERIC_DESC in content:
        # Replace with empty description so Hugo auto-generates from .Summary
        content = content.replace(
            f'description: {GENERIC_DESC}',
            'description: ""'
        )
        content = content.replace(
            f"description: '{GENERIC_DESC}'",
            'description: ""'
        )
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    print("=" * 60)
    print("🔥 FENIX V3 PURGE - FASE 1: LA GRAN PURGA")
    print("=" * 60)
    
    # --- PASO 1: Cuarentena de canibalizados ---
    print("\n📦 PASO 1: Cuarentena de artículos canibalizados...")
    quarantined = 0
    not_found = []
    for filepath in sorted(ALL_PURGE):
        if os.path.exists(filepath):
            inject_draft(filepath)
            quarantined += 1
            print(f"   🔒 DRAFT: {filepath}")
        else:
            not_found.append(filepath)
            print(f"   ⚠️  NOT FOUND: {filepath}")
    
    print(f"\n   ✅ {quarantined} artículos pasados a draft: true")
    if not_found:
        print(f"   ⚠️  {len(not_found)} archivos no encontrados (ya eliminados?)")
    
    # --- PASO 2: Borrado de huellas Pollinations ---
    print("\n🧹 PASO 2: Borrado de huellas Pollinations.ai...")
    pollinations_cleaned = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in files:
            if fname.endswith('.md'):
                fpath = os.path.join(root, fname)
                if remove_pollinations_image(fpath):
                    pollinations_cleaned += 1
                    print(f"   🗑️  POLLINATIONS REMOVED: {fpath}")
    
    print(f"\n   ✅ {pollinations_cleaned} campos image: pollinations eliminados")
    
    # --- PASO 3: Limpieza de meta descriptions genéricas ---
    print("\n📝 PASO 3: Limpieza de meta descriptions genéricas...")
    desc_fixed = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        for fname in files:
            if fname.endswith('.md'):
                fpath = os.path.join(root, fname)
                if fix_generic_description(fpath):
                    desc_fixed += 1
                    print(f"   📝 DESC FIXED: {fpath}")
    
    print(f"\n   ✅ {desc_fixed} meta descriptions genéricas limpiadas")
    
    # --- RESUMEN ---
    print("\n" + "=" * 60)
    print("📊 RESUMEN FASE 1:")
    print(f"   🔒 Artículos cuarentenados: {quarantined}")
    print(f"   🗑️  Huellas Pollinations borradas: {pollinations_cleaned}")
    print(f"   📝 Meta descriptions reparadas: {desc_fixed}")
    print("=" * 60)

if __name__ == "__main__":
    main()
