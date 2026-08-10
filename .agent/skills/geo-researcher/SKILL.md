---
name: geo-researcher
description: Extrae intenciones de búsqueda informativas/transaccionales, preguntas frecuentes (PAA), entidades clave y datos estadísticos verificables antes de redactar.
---

# GEO Researcher Skill

Esta habilidad define el protocolo para realizar investigación sintáctica, de intenciones de búsqueda y extracción de entidades para Generative Engine Optimization (GEO) y Answer Engine Optimization (AEO).

## 🎯 Objetivos de la Skill

1. **Clasificación de Intención de Búsqueda**:
   - **Informacional**: Búsqueda de explicaciones profundas, tutoriales, arquitecturas o conceptos.
   - **Transaccional / Comercial**: Comparativas de productos, guías de compra, precios o benchmarks.
   - **Mixta**: Combinación de entendimiento teórico con aplicación práctica inmediata.

2. **Extracción de PAA (People Also Ask)**:
   - Identificar entre 3 y 5 preguntas reales que los usuarios consultan frecuentemente sobre el tema central.
   - Formatear las preguntas de forma directa e inequívoca para facilitar la generación de bloques FAQ.

3. **Mapeo de Entidades y Grafo de Conocimiento (KG Entities)**:
   - Extraer entidades primarias (marcas, algoritmos, normas, librerías) y entidades secundarias relacionadas.
   - Establecer la terminología técnica obligatoria que debe estar presente en el artículo.

4. **Verificación Estadística y de Fuentes**:
   - Identificar al menos 2 datos estadísticos o métricas numéricas verificables (porcentajes, tiempos de respuesta, benchmarks, años).
   - Atribuir las fuentes a instituciones, estudios oficiales o documentación formal de la industria.

---

## 📄 Estructura del Caché (`research_brief.json`)

El resultado de la investigación debe guardarse obligatoriamente en un archivo `research_brief.json` dentro del bundle del artículo con el siguiente esquema:

```json
{
  "topic": "Nombre del Tema Investigado",
  "search_intent": "informational | transactional | mixed",
  "primary_entity": "Entidad Principal",
  "secondary_entities": [
    "Entidad 1",
    "Entidad 2",
    "Entidad 3"
  ],
  "paa_questions": [
    "¿Pregunta frecuente 1?",
    "¿Pregunta frecuente 2?",
    "¿Pregunta frecuente 3?"
  ],
  "verifiable_stats": [
    {
      "metric": "Descripción del dato estadístico o benchmark",
      "source": "Nombre de la fuente oficial o estudio"
    }
  ],
  "keywords": {
    "primary": "Palabra clave principal",
    "secondary": ["kw1", "kw2", "kw3"]
  }
}
```

---

## 🛠️ Reglas de Ejecución

- **Sin Asunciones**: No inventar estadísticas ni atribuir datos a fuentes inexistentes.
- **Rigor Técnico**: Priorizar documentación oficial y benchmarks verificables por encima de blogs generales.
- **Normalización**: Asegurar que las preguntas PAA estén redactadas de manera clara y natural en el idioma de destino (ES o EN).
