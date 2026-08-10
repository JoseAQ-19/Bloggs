---
name: geo-content-writer
description: Reglas de redacción GEO/AEO/SEO incluyendo Chunking RAG de 40-60 palabras, tablas comparativas, listas estructuradas, sección FAQ y tono E-E-A-T sin muletillas robóticas.
---

# GEO Content Writer Skill

Esta habilidad regula la redacción de contenidos optimizados para motores de búsqueda de Inteligencia Artificial (GEO - Generative Engine Optimization y AEO - Answer Engine Optimization), garantizando máxima citabilidad y alta legibilidad para usuarios humanos.

## 📐 Reglas Estructurales Obligatorias

### 1. Regla del Chunking RAG (Retrieval-Augmented Generation)
- **Ubicación**: Inmediatamente debajo de cada encabezado `## (H2)` y `### (H3)`.
- **Formato**: El primer párrafo debe actuar como un bloque autónomo de respuesta directa.
- **Extensión**: Estrictamente de **40 a 60 palabras**.
- **Resaltado**: Los términos y conceptos clave de la respuesta deben ir marcados en **negrita** para facilitar la extracción semántica por parte de los LLMs.

### 2. Inclusión Obligatoria de Tablas y Listas
- **Tablas Comparativas Markdown**: Cada artículo debe incluir al menos una tabla comparativa en formato Markdown nativo (`| Encabezado 1 | Encabezado 2 |`). No se permiten tablas vacías ni de menos de 3 filas de datos.
- **Listas Estructuradas**: Se exige la presencia de listas ordenadas (`1. 2. 3.`) para procedimientos paso a paso y listas desordenadas (`- `) para características, pros/contras o especificaciones técnicas.

### 3. Sección FAQ (Preguntas Frecuentes)
- **Ubicación**: Al final del artículo, antes del cierre o metodología.
- **Formato**: Encabezado `## Preguntas Frecuentes` conteniendo entre **3 y 4 preguntas frecuentes** (en subencabezados `###`).
- **Respuestas**: Respuestas directas, concisas y orientadas a la intención de búsqueda detectada por el investigativo.

### 4. Tono E-E-A-T y Tolerancia Cero a Muletillas Robóticas
Queda estrictamente **PROHIBIDO** el uso de cliché y muletillas generadas por IA. La presencia de cualquiera de los siguientes patrones provocará el rechazo del contenido:

❌ **Frases Prohibidas**:
- "En el panorama actual..." / "In today's digital landscape..."
- "Un lienzo en blanco..." / "A blank canvas..."
- "Remains to be seen..."
- "Es importante destacar..." / "It's important to note..."
- "Un universo de posibilidades..."
- "Sin duda alguna..." / "Without a doubt..."
- "En resumen..." / "In conclusion..." (como muletilla de cierre de sección)

✅ **Estilo Autorizado**:
- Estilo directo, voz activa, vocabulario técnico preciso y oraciones orientadas a la acción.
- Ejemplos concretos, código probatorio, cifras exactas y explicaciones basadas en la práctica profesional real.
