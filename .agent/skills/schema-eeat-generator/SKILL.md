---
name: schema-eeat-generator
description: Define reglas para estructurar el YAML Frontmatter inyectando schema JSON-LD dinámico (FAQPage, TechArticle, NewsArticle) y asignando un perfil de autor experto por vertical temático.
---

# Schema & E-E-A-T Generator Skill

Esta habilidad define la inyección automatizada de esquemas estructurados JSON-LD y la asignación de señales E-E-A-T (Experiencia, Pericia, Autoridad y Confiabilidad) dentro del YAML Frontmatter de cada publicación de Hugo.

## 🏷️ Estructura del YAML Frontmatter

El Frontmatter de Hugo debe contener tanto las variables nativas del sitio como los objetos de datos para renderizar JSON-LD en el layout `<head>`.

```yaml
---
title: "Título SEO Optimizado (Máx 60 Caracteres)"
description: "Meta descripción relevante y atractiva (120-155 caracteres)."
date: 2026-08-10T12:00:00Z
lastmod: 2026-08-10T12:00:00Z
draft: false
categories: ["Tecnología"]
tags: ["IA", "SEO", "Hugo"]
image: "featured.webp"

# EEAT & Author Details
author:
  name: "Dr. Alex Rivera"
  role: "Senior AI Systems Architect & Cloud Engineer"
  sameAs:
    - "https://www.linkedin.com/in/alexrivera-tech"
    - "https://github.com/arivera-dev"
  bio: "Especialista con más de 12 años de experiencia en infraestructura de IA y sistemas distribuidos."

# Dynamic Schemas
schema:
  type: "TechArticle" # Opciones: TechArticle, NewsArticle, Article
  proficiencyLevel: "Expert"
  dependencies: "Hugo v0.120+, Python 3.11+"
  faq:
    - question: "¿Qué es el RAG Chunking?"
      answer: "Es una técnica de estructuración de texto..."
    - question: "¿Cómo se integra IndexNow?"
      answer: "Mediante una solicitud HTTP POST enviada a..."
---
```

---

## 🤖 Selección de Perfiles de Autor Experto por Vertical

Para cumplir con las directrices YMYL (Your Money Your Life) y E-E-A-T de Google, el autor asignado debe coincidir deterministamente con la categoría del artículo:

| Vertical Temático | Perfil del Autor | Credenciales / Rol |
| :--- | :--- | :--- |
| **Tecnología / Software / IA** | Dr. Alex Rivera | Senior AI Systems Architect & Cloud Engineer |
| **Finanzas / FinTech / Crypto** | Elena Maretti, CFA | Financial Analyst & Quantitative Economist |
| **Salud / Bienestar / Fitness** | Dra. Sophia Chen, MD | Medical Consultant & Performance Specialist |
| **Ciberseguridad / DevSecOps** | Carlos Mendoza | Certified Information Systems Security Professional (CISSP) |
| **General / Tendencias** | Equipo Editorial NovumWorld | Redacción Especializada & Fact-Checking Board |

---

## 📐 Inyección de Schemas JSON-LD Dinámicos

### 1. `FAQPage` Schema
Se genera automáticamente a partir de las preguntas de la sección FAQ del contenido o del bloque `schema.faq` en el Frontmatter:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Pregunta frecuente?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Respuesta directa a la pregunta..."
      }
    }
  ]
}
```

### 2. `TechArticle` / `NewsArticle` Schema
Se inyecta según la naturaleza técnica o noticiosa del contenido:

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Título del Artículo",
  "image": ["https://midominio.com/posts/categoria/slug/featured.webp"],
  "datePublished": "2026-08-10T12:00:00Z",
  "dateModified": "2026-08-10T12:00:00Z",
  "author": {
    "@type": "Person",
    "name": "Dr. Alex Rivera",
    "jobTitle": "Senior AI Systems Architect",
    "sameAs": ["https://www.linkedin.com/in/alexrivera-tech"]
  },
  "publisher": {
    "@type": "Organization",
    "name": "NovumWorld",
    "logo": {
      "@type": "ImageObject",
      "url": "https://midominio.com/images/logo.webp"
    }
  }
}
```
