---
name: hugo-leafbundle-builder
description: Define reglas para estructurar la salida de Hugo en Leaf Bundles (content/posts/{category}/{slug}/index.md) con su imagen local featured.webp y el caché de investigación research_brief.json.
---

# Hugo Leaf Bundle Builder Skill

Esta habilidad establece las especificaciones exactas para organizar los artefactos de contenido generados en la estructura de **Hugo Leaf Bundles**, garantizando el encapsulamiento de recursos locales, imágenes comprimidas y datos de investigación.

## 📂 Estructura del Leaf Bundle

Cada artículo publicado DEBE ser empaquetado exclusivamente dentro de un directorio dedicado bajo la siguiente jerarquía:

```text
content/
└── posts/
    └── {category}/
        └── {slug}/
            ├── index.md             # Contenido principal del artículo en Markdown + Frontmatter
            ├── featured.webp        # Imagen principal optimizada (WebP, máx 100KB)
            └── research_brief.json  # Caché con los datos de investigación GEO/AEO
```

### Ejemplo Concreto:
```text
content/posts/tecnologia/arquitectura-rag-hugo/index.md
content/posts/tecnologia/arquitectura-rag-hugo/featured.webp
content/posts/tecnologia/arquitectura-rag-hugo/research_brief.json
```

---

## 🛠️ Especificaciones de Archivos dentro del Bundle

### 1. `index.md`
- **Requisito**: Es el punto de entrada para Hugo como Leaf Bundle.
- **Ruta de Imagen Interna**: Debe referenciar su propia imagen de cabecera mediante la propiedad `image: "featured.webp"` en el Frontmatter. No utilizar rutas absolutas locales ni URLs externas no verificadas.

### 2. `featured.webp`
- **Formato**: Formato WebP optimizado con relación de aspecto 16:9 (ej. 1200x675 px).
- **Procesamiento**: En caso de no generarse dinámicamente mediante API, se debe copiar la imagen predeterminada de la categoría desde `static/images/defaults/`.
- **Naming**: Debe nombrarse exactamente `featured.webp` dentro del directorio del bundle.

### 3. `research_brief.json`
- **Utilidad**: Conserva la auditoría de intenciones de búsqueda, entidades y datos estadísticos utilizados para generar el artículo.
- **Integración**: Permite a los agentes de corrección y auditoría (`corrector.py`, `seo-auditor-validator`) validar que las promesas del brief se cumplieron en el contenido final.

---

## 🔒 Reglas de Validación de Rutas y Slugs

- **Slugs Sanitizados**: El nombre de la carpeta `{slug}` debe estar en minúsculas, usando exclusivamente guiones ASCII (`-`), sin acentos, espacios ni caracteres especiales.
- **Categorías Normalizadas**: La carpeta `{category}` debe estar alineada con el registro oficial de nichos (`core/niche_registry.py`).
