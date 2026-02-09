import os
import glob
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Cargar entorno
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

try:
    client = genai.Client(api_key=GEMINI_KEY)
except:
    print("❌ Error: No API Key found.")
    exit(1)

PROJECT_ROOT = "/Users/manolo/Bloggs"
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

def read_codebase():
    """Lee los archivos críticos del proyecto."""
    files_to_scan = ["main.py", "researcher.py", "utils.py"]
    code_content = ""
    
    for filename in files_to_scan:
        path = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                code_content += f"\n--- FILE: {filename} ---\n"
                code_content += f.read()
                
    # Scan themes (just listing structure for context)
    theme_path = os.path.join(PROJECT_ROOT, "themes")
    if os.path.exists(theme_path):
        code_content += "\n--- THEME STRUCTURE (Brief) ---\n"
        for root, dirs, files in os.walk(theme_path):
            for file in files:
                if file.endswith(".html") or file.endswith(".css"):
                     code_content += f"File: {os.path.join(root, file)}\n"
                     
    return code_content

def generate_audit_report(code_context):
    print("🧠 Iniciando Auditoría Nocturna con Gemini...")
    
    prompt = f"""
    ACTÚA COMO UN SENIOR SOFTWARE ARCHITECT (CTO).
    Realiza una AUDITORÍA DE CÓDIGO del siguiente proyecto Python + Hugo.
    
    CÓDIGO FUENTE:
    {code_context[:30000]}  # Limitamos contexto para no saturar
    
    TU TAREA:
    Genera un informe Markdown profesional con estas secciones:
    
    1. 🚦 ESTADO DE SALUD (Health Check)
       - Puntúa del 1 al 10 la calidad actual.
       - Detecta "Code Smells" (Duplicación, funciones monolíticas, falta de docs).
       
    2. 🐢 CUELLOS DE BOTELLA (Performance)
       - Identifica lógica bloqueante o ineficiente (ej: requests síncronos, bucles O(n^2)).
       
    3. 🛡️ SEGURIDAD Y ROBUSTEZ
       - ¿Hay manejo de errores? ¿Secretos expuestos?
       
    4. 💡 IDEAS FRESCAS (Next Level)
       - Propón 3 mejoras creativas para implementar mañana (Refactorización o Nuevas Features).
       
    FORMATO: Markdown limpio y directo. Sé crítico pero constructivo.
    """
    
    resp = client.models.generate_content(
        model='gemini-2.0-flash', 
        contents=prompt
    )
    
    return resp.text

def save_report(content):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"auditoria_{date_str}.md"
    path = os.path.join(REPORTS_DIR, filename)
    
    with open(path, "w") as f:
        f.write(content)
    
    print(f"✅ Informe guardado: {path}")

if __name__ == "__main__":
    code = read_codebase()
    report = generate_audit_report(code)
    save_report(report)
