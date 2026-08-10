---
name: responsive-ui-components
description: Estándares y componentes UI responsivos de alto nivel para novumworld.com (grid de noticias asimétrico, menú flotante glassmorphism, barra de lectura, TOC e índice flotante, FAQ acordeón).
---

# 📱 Skill: Responsive UI Components Standard

Esta habilidad define la arquitectura maquetada y accesible de componentes UI para las plantillas Hugo de **novumworld.com**.

---

## 🏛️ 1. Rejilla Asimétrica de Portada (Magazine Grid Layout)

- **Hero Post Destacado**: Ocupa el 66% del ancho superior en desktop (`col-span-8` / `grid-column: span 8`) con la imagen de portada `featured.webp` integrada en alta resolución con superposición translúcida de titulares.
- **Side Trending Feed**: Ocupa el 33% lateral en desktop (`col-span-4`) con una lista compacta de noticias con métricas de tendencias y etiquetas de tiempo relativo ("hace 15 min").
- **Grid de Noticias Secundario**: Rejilla responsiva `repeat(auto-fit, minmax(320px, 1fr))` para tarjetas de categorías.

---

## 🧭 2. Header Flotante Semi-Transparente (Glass Navbar)

- **Fijo en Top (`position: sticky; top: 0; z-index: 100`)**.
- **Efecto Blur**: `background: rgba(7, 9, 14, 0.75); backdrop-filter: blur(16px)`.
- **Navegación por Silos**: Submenús redondeados tipo *pills* con resaltado de la categoría activa.
- **Selector de Idioma Dinámico**: Switcher discreto EN / ES con bandera/etiqueta accesible.

---

## 📖 3. Componentes Inmersivos para Artículos (`single.html`)

1. **Barra de Progreso de Lectura (`.reading-progress`)**:
   - Barra fija en la parte superior `height: 3px` con gradiente cian a violeta (`linear-gradient(90deg, #00F0FF, #7000FF)`).
   - Se llena dinámicamente con JS según el scroll vertical del usuario (`window.scrollY / totalHeight`).

2. **Índice Flotante (Table of Contents - TOC)**:
   - Sticky sidebar con los encabezados `H2` del artículo.
   - Resalta dinámicamente la sección activa durante la lectura.

3. **Cajas de Datos Destacados (TL;DR / Key Metrics Data Boxes)**:
   - Cajas resaltadas con borde cian translúcido e icono de IA (`#00F0FF`).
   - Presenta resúmenes clave de 40-60 palabras o viñetas cuantitativas antes del cuerpo principal.

4. **Acordeón FAQ (Preguntas Frecuentes)**:
   - Componente colapsable interactivo `<details class="faq-item"> <summary>...` estilizado con animaciones de apertura suave y Schema JSON-LD `FAQPage` reflejado en HTML.
