import os
keys = [
    "GEMINI_API_KEY",
    "MODELS_TOKEN_CEU",
    "TOKEN_MODELS",
    "TOGETHER_API_KEY",
    "HUGGINGFACE_API_KEY",
    "EXA_API_KEY",
    "OPEN_ROUTER_API_KEY",
    "NVIDIA_API_KEY",
]
for k in keys:
    val = os.getenv(k)
    print(f"{k}: {'SET (len=' + str(len(val)) + ')' if val else 'NOT SET'}")
