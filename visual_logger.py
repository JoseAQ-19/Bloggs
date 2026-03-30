import os
import json
from datetime import datetime

class VisualLogger:
    """
    Guarda los prompts generados por el Extractor Visual y sus metadatos
    para trazabilidad y depuración posterior.
    """
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "visual")

    @classmethod
    def log(cls, slug: str, category: str, title: str, prompt: str, provider: str, status: str = "success"):
        try:
            os.makedirs(cls.LOG_DIR, exist_ok=True)
            log_file = os.path.join(cls.LOG_DIR, "image_prompts.jsonl")
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "slug": slug,
                "category": category,
                "title": title,
                "provider": provider,
                "prompt": prompt,
                "status": status
            }
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            print(f"⚠️ [VisualLogger] Error al guardar log visual: {e}")
