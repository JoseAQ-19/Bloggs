import os
from together import Together
from dotenv import load_dotenv

# Cargar .env explícitamente para asegurar
load_dotenv()

def test_raw():
    print("🧪 TEST VERDAD DESNUDA (TOGETHER AI)...")
    
    key = os.environ.get("TOGETHER_API_KEY")
    print(f"🔑 TOGETHER_API_KEY detectada: {bool(key)}")
    if key:
        print(f"📏 Longitud de la clave: {len(str(key))}")
        print(f"🔒 Primeros 5 chars: {str(key)[:5]}...")
    
    print("\n🚀 Intentando Generación DIRECTA (Sin red)...")
    
    client = Together(api_key=key)
    
    # Llamada que debe explotar si algo va mal
    response = client.images.generate(
        prompt="A cute robot holding a sign that says ERROR TEST, 8k, realistic",
        model="black-forest-labs/FLUX.1-schnell",
        width=1024,
        height=768,
        steps=4,
        n=1,
        response_format="b64_json"
    )
    
    print("✅ ¡ÉXITO! Se generó la imagen (no hubo crash).")
    print(f"📦 Payload recibido. Longitud B64: {len(response.data[0].b64_json)}")

if __name__ == "__main__":
    test_raw()
