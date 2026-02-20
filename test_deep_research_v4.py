
import os
import sys
import time
from dotenv import load_dotenv

# Asegurar que importamos del repo local
sys.path.append(os.getcwd())

from researcher import Researcher, build_research_query

load_dotenv()

def test_deep_research():
    print("🚀 PROBANDO NOTEBOOKLM DEEP RESEARCH PROTOCOL (V4 + TRIFORCE)")
    
    res = Researcher()
    
    # Parámetros de prueba
    topic = "The real impact of Llama 3.3 70B on private local LLM deployments"
    cat = "ia"
    lang = "en"
    
    print(f"🎯 TEMA: {topic}")
    print(f"🌍 IDIOMA: {lang}")
    
    # 1. Probar el Keyword Miner (Triforce)
    print("\n--- 1. PROBANDO TRIFORCE MINER ---")
    super_topic = res.v4._mine_deep_keywords(topic, lang)
    print(f"✨ Super-Query: {super_topic}")
    
    # 2. Construir el Brief
    print("\n--- 2. CONSTRUYENDO BRIEF E-E-A-T ---")
    brief = build_research_query(super_topic, cat, "LLM security private deployment local model", lang=lang)
    print("Brief generado (preview):")
    print(brief[:200] + "...")
    
    # 3. Lanzar Capa 1 (DEEP Research)
    print("\n--- 3. EJECUTANDO CAPA 1: NotebookLM DEEP MODE ---")
    print("Nota: Esto tardará varios minutos si funciona correctamente.")
    
    result = res.v4._layer_1_notebooklm(super_topic, brief, lang)
    
    if result:
        print("\n🏆 COMPLETADO CON ÉXITO!")
        print(f"📊 Capa usada: {result.get('layer')}")
        print(f"📄 Contenido (primeros 1000 chars):\n")
        print("-" * 50)
        print(result['content'][:1000] + "...")
        print("-" * 50)
        
        # Guardar en un log para revisar
        with open("research_test_result.md", "w", encoding="utf-8") as f:
            f.write(f"# RESEARCH TEST: {topic}\n\n")
            f.write(f"**Super Query:** {super_topic}\n\n")
            f.write(result['content'])
        print(f"\n✅ Resultado completo guardado en research_test_result.md")
    else:
        print("\n❌ FALLO TOTAL: La Capa 1 no devolvió resultados.")
        print("Revisa los logs anteriores para ver si falló el polling, la conexión MCP o la extracción.")

if __name__ == "__main__":
    test_deep_research()
