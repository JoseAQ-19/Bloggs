import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# OmniRoute AI Gateway Settings (Local Primary Router)
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:8000/v1")
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "sk-omniroute")
LLM_MODEL = os.getenv("LLM_MODEL", "auto")
OMNIROUTE_MODELS = [LLM_MODEL, "auto/coding", "auto"]
