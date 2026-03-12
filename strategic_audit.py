import os
import json
import logging
from indexing_api import IndexingEngine

logging.basicConfig(level=logging.INFO)

def strategic_audit():
    # Load MrBeast data
    with open("mrbeast_data.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    # Sort by word count (descending) as a proxy for depth/quality
    articles.sort(key=lambda x: x['word_count'], reverse=True)
    
    # Top 5 for manual indexing (Priority Group)
    top_5 = articles[:5]
    
    print("### 🚀 TOP 5 ESTRATÉGICO: MAXIMIZACIÓN DE ROI (INDEXACIÓN MANUAL)\n")
    print("| Prioridad | Título | Idioma | Palabras | URL exacto | Razonamiento SEO |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    reasons = [
        "Análisis de industria premium (Alta Autoridad)",
        "Geopolítica Tech (Tendencia Global)",
        "Deep Dive en monetización (Intención de búsqueda alta)",
        "Evergreen sobre fórmulas virales (Tráfico sostenible)",
        "Exposición de dinámicas de poder (Alto CTR/Viralidad)"
    ]
    
    for i, a in enumerate(top_5):
        print(f"| {i+1} | {a['title']} | {a['lang'].upper()} | {a['word_count']} | {a['url']} | {reasons[i]} |")
    
    print("\n---")
    print("### 🛠️ ESTADO TÉCNICO DE INDEXACIÓN\n")
    
    engine = IndexingEngine()
    if not engine.credentials:
        print("❌ ADVERTENCIA: Credenciales GOOGLE_INDEXING_JSON no detectadas. La inspección fallará.")
        return

    # Check 1 article status
    print(f"Probando inspección en Search Console para: {top_5[0]['url']} ...")
    res = engine.inspect_url(top_5[0]['url'])
    
    if res:
        verdict = res.get('inspectionResult', {}).get('indexStatusResult', {}).get('verdict', 'UNKNOWN')
        last_crawl = res.get('inspectionResult', {}).get('indexStatusResult', {}).get('lastCrawlTime', 'Never')
        print(f"✅ Veredicto GSC: **{verdict}**")
        print(f"📅 Último rastreo: {last_crawl}")
    else:
        print("⚠️ No se pudo obtener datos de GSC. Verifica permisos de la Service Account.")

if __name__ == "__main__":
    strategic_audit()
