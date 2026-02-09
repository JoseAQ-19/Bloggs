# 🛡️ AUDITORÍA TÉCNICA Y DE ARQUITECTURA (CTO REPORT)
**Fecha:** 2026-02-09
**Proyecto:** Bloggs (Automated Content Agency)
**Arquitectura:** Python (Orchestrator) + Hugo (SSG) + Gemini 2.0 (LLM) + NotebookLLM (RAG)

---

## 🚨 RESUMEN EJECUTIVO
El sistema actual ha evolucionado de un script simple ("Francotirador") a una agencia de contenidos capaz de generar clusters ("Planificador Urbano"). Sin embargo, la infraestructura subyacente sigue siendo frágil.
Estamos operando en **Modo Prototipo**. Para escalar a producción masiva y competir en SEO en 2026, necesitamos robustecer la **ingestión de datos**, la **resiliencia ante fallos** y la **entrega de activos (imágenes)**.

---

## 🔴 CRÍTICO (Prioridad Inmediata)
*Fallo inminente o pérdida de valor SEO grave.*

### 1. Hotlinking de Imágenes (Pollinations.ai)
*   **Problema:** Estamos usando URLs directas (`https://image.pollinations.ai/...`) en el Front Matter.
*   **Riesgo:**
    *   **SEO:** Google penaliza el CLS (Cumulative Layout Shift) si las imágenes no tienen dimensiones fijas o tardan en cargar desde terceros.
    *   **Disponibilidad:** Si Pollinations cambia su API, borra caché o cae, **TODAS las imágenes del blog desaparecen**.
*   **Solución Propuesta:** Implementar un **Image Downloader & Optimizer** en `main.py`. Descargar la imagen, convertirla a WebP localmente (`static/images/posts/`) y referenciarla como recurso local.

### 2. Falta de Transaccionalidad (Atomicidad)
*   **Problema:** El script borra la keyword de `keywords.txt` **al principio**. Si el script falla a mitad (ej: Timeout de Gemini generando el Spoke 2), perdemos la keyword y el cluster queda incompleto.
*   **Solución Propuesta:** Implementar patrón **"Peek & Commit"**.
    1.  Leer keyword sin borrar.
    2.  Generar todo el contenido en memoria.
    3.  Guardar archivos MD.
    4.  **Solo al final**, mover keyword a `completed.txt` y borrar de `keywords.txt`.

### 3. Vulnerabilidad de "Alucinación de Enlaces"
*   **Problema:** Confiamos en que Gemini escriba bien los enlaces Markdown `[Link](/posts/...)`. A veces los LLMs ponen espacios, cambian mayúsculas o inventan slugs.
*   **Solución Propuesta:** **Post-Procesamiento con Regex.** Una función Python que escanee el MD generado, busque los placeholders de enlaces y verifique que coinciden *exactamente* con los slugs generados en la fase de planificación.

---

## 🟡 ALTO VALOR (Eficiencia y Tráfico)
*Mejoras de arquitectura que pagan dividendos a largo plazo.*

### 4. Arquitectura de "Page Bundles" (Hugo)
*   **Problema:** Todo va a `content/posts/*.md`. Cuando tengamos 1,000 artículos, esa carpeta será inmanejable.
*   **Oportunidad:** Usar **Leaf Bundles**.
    *   Estructura: `content/posts/{slug}/index.md` + `content/posts/{slug}/featured.webp`.
    *   Ventaja: Cada post es una carpeta autocontenida con sus imágenes. Facilita backups y gestión.

### 5. Caché de Investigación (NotebookLLM)
*   **Problema:** Cada ejecución hace RAG nuevo. Si queremos actualizar un post antiguo o sacar otro ángulo del mismo tema, gastamos tokens y tiempo.
*   **Solución:** Guardar el `research_brief.json` en la carpeta del post (como un archivo de datos adjunto). Esto crea una "Memoria Institucional" del proyecto.

### 6. Taxonomía Dinámica (Silos SEO)
*   **Problema:** Categorías genéricas ("Tecnología").
*   **Solución:** Que la Fase de Planificación sugiera también la **Categoría**.
    *   Ej: "IA en Medicina" -> `categories: ["Salud Digital"]`.
    *   Esto crea silos temáticos naturales que Google adora.

---

## 🟢 OPCIONAL (Calidad de Vida)
*Nice to have.*

### 7. Notificaciones de Estado
*   Enviar un mensaje a Telegram/Discord (vía Webhook) cuando termine un cluster: *"✅ Cluster 'IA Medicina' generado (3 posts). Ver aquí."*

### 8. CLI Arguments
*   Poder correr `python3 main.py --topic "Futuro del Bitcoin"` para saltarse la cola y generar algo urgente bajo demanda.

---

## 🛠️ HOJA DE RUTA TÉCNICA (Siguientes Pasos)

Recomiendo atacar los puntos **CRÍTICOS** en este orden:
1.  **Refactor de Atomicidad:** Asegurar que no perdemos keywords.
2.  **Gestor de Imágenes Local:** Dejar de depender de Pollinations en tiempo real.
3.  **Page Bundles:** Cambiar la estructura de carpetas antes de tener demasiados posts.

*Firmado: Tu CTO Virtual.*
