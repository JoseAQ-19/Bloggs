---
name: graphify-navigator
description: Protocolo de navegación basado en Grafo de Conocimiento para consultar dependencias y arquitectura ahorrando tokens.
---

# Protocolo Graph-First para Antigravity

## 1. Regla de Consulta Previa (Anti-Token Waste)
- **NO hagas búsquedas ciegas (`grep` o lecturas masivas de archivos)** para entender la arquitectura o las dependencias del proyecto.
- Consulta primero el informe estructurado en `graphify-out/GRAPH_REPORT.md` o el archivo `graphify-out/graph.json` para identificar qué módulos, funciones o plantillas están directamente vinculados con la tarea.

## 2. Detección de Impacto de Cambios
- Antes de modificar un archivo crítico (ej. `orchestrator.py`, `llm_router.py`, `novum_visual.py` o layouts de Hugo), revisa sus nodos vecinos en el grafo para prever qué otros scripts o workflows se verán afectados.

## 3. Actualización Incremental
- Tras realizar cambios arquitectónicos o agregar nuevos módulos/secciones, ejecuta `graphify update` para mantener el grafo sincronizado con coste mínimo.
