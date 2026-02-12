import os
import frontmatter
import base64
import time
from dotenv import load_dotenv
from together import Together

# Cargar entorno
load_dotenv()

TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_KEY:
    print("❌ ERROR CRÍTICO: No se encontró TOGETHER_API_KEY. Abortando.")
    exit(1)

client = Together(api_key=TOGETHER_KEY)

CONTENT_ROOT = "content"
STATIC_IMAGES_ROOT = "static/images"

# Crear directorio si no existe
os.makedirs(STATIC_IMAGES_ROOT, exist_ok=True)

def generate_smart_prompt(text_extract):
    """Usa Llama-3 para crear un prompt visual único basado en el texto."""
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[
                {"role": "system", "content": "You are an Expert Art Director for a high-end tech magazine. Your job is to write image generation prompts."},
                {"role": "user", "content": f"Analyze this article excerpt and write a DETAILED image generation prompt (English) for FLUX.1. The image should be cinematic, photorealistic, 8k, and capture the specific essence of the topic. NO text inside the image. Excerpt: '{text_extract[:800]}...'"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"   ❌ Error generando prompt de texto: {e}")
        return None

def generate_image_flux(prompt, filepath):
    """Genera la imagen con FLUX y la guarda."""
    try:
        response = client.images.generate(
            prompt=prompt,
            model="black-forest-labs/FLUX.1-schnell",
            width=1280,
            height=720,
            steps=4,
            n=1,
            response_format="b64_json"
        )
        
        b64_data = response.data[0].b64_json
        image_bytes = base64.b64decode(b64_data)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        
        return True
    except Exception as e:
        print(f"   ❌ Error generando imagen FLUX: {e}")
        return False

def smart_regenerate():
    print("☢️ INICIANDO RENACIMIENTO VISUAL (SMART PROMPTING)...")
    
    count = 0
    success_count = 0
    
    for root, dirs, files in os.walk(CONTENT_ROOT):
        for filename in files:
            if not filename.endswith(".md") or filename.startswith("_index"): continue
            
            filepath = os.path.join(root, filename)
            count += 1
            
            try:
                post = frontmatter.load(filepath)
                title = post.get('title', 'Untitled')
                slug = filename.replace('.md', '')
                content_text = post.content.strip()
                
                if not content_text:
                    print(f"⚠️ Saltando {filename}: Contenido vacío.")
                    continue

                print(f"\n🎨 Procesando: {title[:40]}...")

                # 1. ANÁLISIS DE CONTENIDO (Llama-3)
                print("   🧠 Analizando texto y creando prompt...")
                visual_prompt = generate_smart_prompt(content_text)
                
                if not visual_prompt:
                    print("   ❌ Falló la generación del prompt. Saltando.")
                    continue
                
                # Añadir estilo base para asegurar calidad
                final_prompt = f"{visual_prompt}, cinematic lighting, highly detailed, 8k render, photorealistic, wide angle"

                # 2. GENERACIÓN VISUAL (FLUX)
                img_filename = f"{slug}.jpg"
                img_phys_path = os.path.join(STATIC_IMAGES_ROOT, img_filename)
                
                print("   🖌️ Pintando con FLUX...")
                if generate_image_flux(final_prompt, img_phys_path):
                    
                    # 3. VERIFICACIÓN
                    if os.path.exists(img_phys_path) and os.path.getsize(img_phys_path) > 100000:
                        # 4. ENLACE ROBUSTO
                        new_rel_path = f"/images/{img_filename}"
                        post['featured_image'] = new_rel_path
                        
                        with open(filepath, 'wb') as f:
                            frontmatter.dump(post, f)
                            
                        print(f"   ✅ ÉXITO: Imagen única generada y enlazada.")
                        success_count += 1
                    else:
                        print(f"   ❌ ERROR VERIFICACIÓN: La imagen generada es demasiado pequeña o no existe.")
                else:
                    print("   ❌ Fallo en generación de imagen.")

            except Exception as e:
                print(f"   ❌ ERROR CRÍTICO en {filename}: {e}")

    print(f"\n☢️ RENACIMIENTO FINALIZADO. {success_count}/{count} posts renovados.")

if __name__ == "__main__":
    smart_regenerate()
