# NovumWorld: Plataforma de Periodismo de Datos Aumentado por IA

NovumWorld es un medio digital de vanguardia especializado en el análisis profundo de tendencias tecnológicas, financieras y de estilo de vida. Nuestra misión es transformar datos complejos en información accionable para una audiencia global.

## 🚀 Misión y Visión
Combinamos el análisis humano estratégico con modelos avanzados de procesamiento de datos para ofrecer perspectivas que otros medios pasan por alto. No nos conformamos con el "qué", explicamos el "por qué".

## 📊 Nuestra Metodología
Nuestra redacción utiliza una infraestructura de datos propietaria para:
- **Auditoría de Fuentes:** Verificación cruzada de datos financieros y macroeconómicos en tiempo real.
- **Análisis de Sentimiento:** Seguimiento de tendencias globales en mercados emergentes y tecnología IA.
- **EEAT First:** Priorizamos la Experiencia, Pericia, Autoridad y Confiabilidad en cada pieza editorial.

## 💻 Arquitectura Técnica y Estructura del Proyecto

El ecosistema de NovumWorld está estructurado en módulos limpios y desacoplados para garantizar alta mantenibilidad, trazabilidad y ejecución sin errores en CI/CD:

```text
Bloggs-1/
├── core/                       # Núcleo lógico y motores principales de IA
│   ├── __init__.py
│   ├── orchestrator.py         # Orquestador del pipeline de generación y guardado
│   ├── llm_router.py           # Enrutador OmniRoute y gestión de fallbacks LLM
│   ├── novum_visual.py         # Motor visual y compresión WebP (<150 KB)
│   ├── researcher.py           # Motor de investigación bilingüe y NotebookLM MCP
│   ├── niche_registry.py       # Registro de nichos, silos jerárquicos y autores E-E-A-T
│   ├── utils.py                # Gestor de enlaces internos y footer determinista
│   ├── prompts_factory.py      # Fábrica de prompts bilingües y reglas GEO/AEO 2026
│   ├── prompts_tools.py        # Blueprints de diseño y componentes dinámicos
│   ├── content_engine_pro.py   # Motor de redacción pro para AdSense
│   ├── text_cleaner.py         # Sanitizador de huella IA y markdown
│   ├── visual_context_extractor.py # Extractor de contexto visual y entidades
│   ├── visual_logger.py        # Logging estructurado de generación visual
│   ├── chart_engine.py         # Generador de gráficos de datos financieros
│   ├── api_cache.py            # Caché de peticiones a APIs
│   └── config.py               # Configuración global y variables de entorno
├── scripts/                    # Scripts ejecutables de pipelines y utilidades
│   ├── trend_scout.py          # Buscador de tendencias pre-investigadas
│   ├── trend_hunter.py         # Buscador de tendencias en vivo
│   ├── qa_orchestrator.py      # Orquestador de QA y Corrector
│   ├── qa_editor_es.py         # Corrección editorial en español
│   ├── qa_editor_en.py         # Corrección editorial en inglés
│   ├── stocks_scout.py         # Scout del vertical de Fondos de Inversión
│   ├── stocks_writer.py        # Redactor del vertical de Fondos
│   ├── run_mrbeast.py          # Newsjacking del vertical YouTube (ES)
│   ├── run_mrbeast_en.py       # Newsjacking del vertical YouTube (EN)
│   ├── audit_v2.py             # Auditor estático de E-E-A-T y SEO
│   └── ...
├── tests/                      # Suite completa de tests unitarios e integración
│   ├── conftest.py             # Configuración de sys.path y entorno pytest
│   ├── test_api_retry.py       # Tests de resiliencia y fallbacks LLM
│   ├── test_data_finance.py    # Tests de integración financiera (yfinance / DefiLlama)
│   ├── test_data_pubmed.py     # Tests de investigación médica (PubMed API)
│   ├── test_data_youtube.py    # Tests de transcripción de YouTube
│   ├── test_fix_index_urls.py  # Tests de normalización de URLs
│   ├── test_geo_aeo.py         # Tests de reglas GEO/AEO 2026 y Frontmatter
│   ├── test_json_cache.py      # Tests de caché JSON y validez de títulos
│   ├── test_nvidia_integration.py # Tests de integración con NVIDIA NIM
│   ├── test_purge_and_clean.py # Tests de purga y calidad de artículos
│   ├── test_qa_link_validator.py # Tests de validación de hipervínculos
│   ├── test_router.py          # Tests de enrutamiento LLMRouter
│   └── test_visual.py          # Tests de compresión WebP y Hugo Leaf Bundles
├── docs/                       # Documentación técnica y auditorías
│   └── audits/                 # Reportes secundarios e informes de auditoría AdSense
├── content/                    # Artículos publicados en Hugo Leaf Bundles
│   ├── es/                     # Contenido en Español (content/es/{category}/{slug}/index.md)
│   └── en/                     # Contenido en Inglés (content/en/{category}/{slug}/index.md)
├── .github/workflows/          # Matrices de orquestación en GitHub Actions
│   ├── scout.yml               # Workflow del Scout Matrix
│   ├── writer.yml              # Workflow del Writer Matrix
│   ├── corrector.yml           # Workflow del Corrector Matrix
│   └── newsjacking-mrbeast-*.yml # Workflows de Newsjacking
├── main.py                     # Punto de entrada principal (Pipeline General)
├── stocks_main.py              # Punto de entrada para Fondos de Inversión
└── progress.txt                # Registro de estado de desarrollo y tareas completadas
```

---

*© 2026 NovumWorld Editorial Group. Todos los derechos reservados.*