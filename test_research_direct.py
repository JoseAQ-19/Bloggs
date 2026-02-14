
import os
import sys
# Simular entorno para que importe bien
sys.path.append(os.getcwd())

from researcher import ResearcherV3

def test_notebooklm_flow():
    print("🧪 INICIANDO PRUEBA DE CONCEPTO: NotebookLM Research Flow")
    
    researcher = ResearcherV3()
    
    # Tema de prueba
    topic = "GPT-5 Release Date Predictions 2025"
    print(f"🎯 Tema de Prueba: {topic}")
    
    # Forzar uso de NotebookLM (Capa 1)
    # ResearcherV3.research() llama internamente a _layer_1_notebooklm
    result = researcher._layer_1_notebooklm(topic)
    
    if result:
        print("\n✅ PRUEBA EXITOSA: NotebookLM ha investigado y generado contenido.")
        print("--- RESUMEN DEL CONTENIDO GENERADO ---")
        print(result['content'][:500] + "...")
        print("--------------------------------------")
        return True
    else:
        print("\n❌ PRUEBA FALLIDA: No se pudo completar la investigación con NotebookLM.")
        return False

if __name__ == "__main__":
    test_notebooklm_flow()
