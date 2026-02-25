# Product Requirements Document (PRD): Sistema Autónomo de Blogs (AdSense)

## 1. Análisis del Estado Actual y Ruta Tecnológica Óptima

**Estado Actual:**
Tras analizar el espacio de trabajo `Bloggs`, la arquitectura del proyecto se basa en:
*   **Generador de Sitios Estáticos (SSG):** Hugo (evidenciado por directorios `content/`, `layouts/`, `themes/`, `static/`).
*   **Hosting / Despliegue:** Vercel (presencia de `vercel.json`, `vercel-ignore.sh`).
*   **Orquestación:** GitHub Actions (`.github/workflows/`) encadenando procesos "Scout" (cazadores de tendencias) y "Writer" (redactores).
*   **Motor Lógico:** Python (`main.py`, `trend_scout.py`, `researcher.py`) con múltiples agentes LLM (Gemini dominante, fallbacks a OpenRouter/Zhipu).
*   **Persistencia de datos:** Git. Las tendencias y artículos se guardan como JSON/Markdown y se hacen commits para disparar el siguiente paso.

**Ruta Tecnológica Más Óptima, Robusta y Escalable:**
La arquitectura actual "Headless CMS + GitOps + Serverless" es la **más óptima para AdSense** porque asegura tiempos de carga ultrarrápidos (Core Web Vitals), costo cero en base de datos de infraestructura y seguridad total.
*Lo que falta para terminar el sistema* y hacerlo 100% autónomo (Ralph Loop ready) es la robustez en la ejecución: manejo de errores sin intervención humana, validación estricta del output de los LLM (evitar "ghost articles" o YAML corrompido) y un control de concurrencia en los commits de GitHub Actions.



## 2. Desarrollo por Tareas Atómicas (Metodología Ralph Loop)

A continuación, la división del trabajo en tareas extremadamente aisladas. Cada tarea está diseñada con un **Criterio de Éxito Binario** para que el agente autónomo (Ralph Loop) pueda verificar si pasa o no pasa y detener su bucle.

### Fase 1: Robustez de la Capa de Orquestación y API

- [ ] **Tarea 1.1: Implementar sistema de reintentos (Exponential Backoff) en APIs LLM y de búsqueda.**
  - **Contexto:** Las llamadas a Gemini, Exa o OpenRouter pueden fallar por Rate Limits (429) o errores del servidor (5xx).
  - **Manejo de Errores Requerido:** Si la API principal falla, reintentar 3 veces con espera de 2s, 4s y 8s. Si sigue fallando, activar el motor secundario. Si el secundario falla, registrar error crítico y abortar ejecución limpiamente (sin corromper estado).
  - **Criterio de Éxito:** Ejecutar `pytest test_api_retry.py`. Debe simular un código HTTP 429 temporal, recuperar la llamada y devolver HTTP 200 en menos de 10 segundos.

- [ ] **Tarea 1.2: Resolución de concurrencia en subidas a Git (Evitar colisiones de commits).**
  - **Contexto:** Múltiples workflows de GitHub Actions (`writer-*.yml`) pueden intentar hacer git commit al mismo tiempo hacia el repositorio, provocando errores de colisión.
  - **Manejo de Errores Requerido:** Si el `git push` falla por un estado desactualizado (rejected), ejecutar automáticamente `git pull --rebase` y reintentar el push hasta 5 veces.
  - **Criterio de Éxito:** Ejecutar script E2E de concurrencia. Código de salida (Exit code) de ambos flujos debe ser `0` (Success).

### Fase 2: Robustez de Generación de Contenido y YAML Frontmatter

- [ ] **Tarea 2.1: Validación estricta del YAML Frontmatter antes del guardado.**
  - **Contexto:** Si el LLM genera comillas sin escapar en el título dentro del Markdown, Hugo fallará al compilar y el artículo ("Ghost Article") no se publicará.
  - **Manejo de Errores Requerido:** Interceptar el texto del LLM, aislar el bloque YAML y parsearlo con la librería `yaml` o `ruamel.yaml` de Python. Si el parseo lanza excepción, el sistema debe regenerar o escapar las comillas automáticamente antes de guardar el `.md`.
  - **Criterio de Éxito:** Ejecutar `python validate_yaml_strict.py` sobre un directorio de prueba. El script debe retornar `Exit Code 0` y todos los archivos deben ser leídos sin `YAMLError`.

- [ ] **Tarea 2.2: Verificación de Markdown y Estructura Mínima (Anti-Alucinación).**
  - **Contexto:** El sistema puede generar respuestas vacías, o con formato incompleto (ej. el LLM devuelve un mensaje de error como contenido del artículo o incumple la longitud).
  - **Manejo de Errores Requerido:** Comprobar que el archivo generado supera las 1200 palabras y contiene exactamente los 7 headers H2 definidos. Si no cumple, no hacer commit, borrar el archivo, y reportar la tarea como fallida pero controlada.
  - **Criterio de Éxito:** Ejecutar `python validate_structure.py --file ruta_test.md`. Salida esperada: `stdout="PASS"` y `Exit Code 0`.

### Fase 3: Integración de Imágenes y SEO para AdSense

- [ ] **Tarea 3.1: Automatización y Optimización de Imágenes Destacadas (WebP).**
  - **Contexto:** Novum Visual genera imágenes, pero para AdSense y rendimiento de Hugo, deben ser optimizadas.
  - **Manejo de Errores Requerido:** Si la generación de imagen (DALL-E, Midjourney, etc.) falla o agota créditos, el sistema debe asignar una imagen estática de fallback del directorio `/static/fallbacks/` en lugar de romper el build de Hugo.
  - **Criterio de Éxito:** Ejecutar `python test_image_pipeline.py`. Debe validar que se asigna una imagen válida en `.webp`, de tamaño inferior a 150kb, garantizando el render de Hugo en `Exit Code 0`.

- [ ] **Tarea 3.2: Inyección de Zonas Seguras de AdSense y Enlaces Internos.**
  - **Contexto:** Falla la inyección de la estructura de Spiderweb (enlaces internos) o de marcadores de publicidad que rompen el HTML de la página en Hugo.
  - **Manejo de Errores Requerido:** Validar que los enlaces internos devueltos por la fase 2 apuntan a rutas relativas existentes en el proyecto. Eliminar enlaces internos rotos (404 predictivo) antes de guardarlos.
  - **Criterio de Éxito:** El comando de build local `hugo --renderToMemory --buildDrafts` debe finalizar con estado `0` y 0 errores de "page not found" en referencias internas.

---

## 3. Directrices de Ejecución para el Bucle Autónomo (Ralph Loop)

Para que el agente pueda operar sin tu intervención de forma segura, el sistema se regirá por la ley de **Fallo Controlado (Fail-Safe)**:
1. **Evitar la corrupción del estado:** Nunca hacer commit ni push de archivos parciales.
2. **Logs estructurados:** Todos los scripts de Python deben exportar sus excepciones en un archivo `error_report.json` para que Ralph pueda leer `{"component": "gemini", "error": "rate_limit", "action": "retry"}` e iterar el código.
3. **El Árbitro Definitivo:** Ralph Loop solo pasará a la siguiente tarea si el `Exit Code` de la prueba es `0`. Si es distinto de `0`, deberá leer el stderr, aplicar el hotfix pertinente y repetir la prueba hasta lograr su objetivo.
