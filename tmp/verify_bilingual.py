
import os
import sys

# Añadir el path actual para que pueda importar módulos locales
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "scripts"))

from prompts_factory import PromptFactory

def test_bilingual_prompts():
    print("═══ TEST DE BILINGÜISMO EN PROMPTS (MASTERPIECE) ═══\n")
    
    # 1. Probar Nicho IA en ESPAÑOL
    prompt_es = PromptFactory.get_system_prompt("ia", "es")
    print("--- [ESPAÑOL: ia] ---")
    if "## Resumen Ejecutivo" in prompt_es:
        print("✅ Header de resumen en ESPAÑOL detectado.")
    else:
        print("❌ ERROR: No se encontró '## Resumen Ejecutivo' en el prompt de ES.")
    
    # 2. Probar Nicho IA en INGLÉS
    prompt_en = PromptFactory.get_system_prompt("ia", "en")
    print("\n--- [INGLÉS: ia] ---")
    if "## Executive Summary" in prompt_en:
        print("✅ Header de resumen en INGLÉS detectado.")
    else:
        print("❌ ERROR: No se encontró '## Executive Summary' en el prompt de EN.")
        
    # 3. Verificación de directivas adicionales (Simulando Orchestrator)
    if "## Resumen Ejecutivo" in prompt_es and "## Executive Summary" in prompt_en:
        print("\n💎 CONCLUSIÓN: La factoría de prompts está correctamente localizada.")
    else:
        print("\n⚠️ ADVERTENCIA: Hay inconsistencias en la factoría.")

if __name__ == "__main__":
    test_bilingual_prompts()
