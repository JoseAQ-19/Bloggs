---
name: threejs-3d-hero
description: Mejores prácticas y guía de implementación para escenas WebGL/Three.js 3D interactivas y ultraligeras en la portada (Hero Section) de novumworld.com con rendimiento de 60 FPS sin penalizar Core Web Vitals ni SEO.
---

# 🧊 Skill: 3D Animation & WebGL Hero Standard (Three.js)

Esta habilidad especifica los estándares técnicos para la creación de experiencias 3D fotorrealistas e interactivas en la portada principal de **novumworld.com**.

---

## ⚡ 1. Principios de Rendimiento y Core Web Vitals (60 FPS Standard)

1. **Carga Diferida & Async Loading**:
   - Cargar Three.js o el engine 3D de forma no bloqueante (`async`/`defer` o ESM import dinámico tras el `DOMContentLoaded`).
   - El renderizado 3D no debe bloquear el First Contentful Paint (FCP) ni el Largest Contentful Paint (LCP) de la página.

2. **Loop Optimizado (`requestAnimationFrame`)**:
   - Usar `requestAnimationFrame` para la animación continuada.
   - Pausar la animación automáticamente con `IntersectionObserver` cuando el canvas del Hero no sea visible en pantalla para ahorrar GPU/Batería.

3. **Interacción Sutil con Cursor (Mouse Tracking)**:
   - Capturar el movimiento del ratón con amortiguación suave (spring lerp: `targetX += (mouseX - targetX) * 0.05`) para evitar saltos o aceleraciones bruscas.
   - Limitar la rotación o desplazamiento del objeto 3D a un rango estrecho (ej. `-0.35` a `+0.35` rads).

4. **Soporte Móvil & Accessibilidad (Fallback System)**:
   - Detectar dispositivos de bajo rendimiento o configuración `prefers-reduced-motion: reduce`.
   - Renderizar un canvas 2D sutil o fondo degradado animado con CSS sin instanciar la escena 3D pesada en dispositivos con recursos limitados.

---

## 🌐 2. Conceptos de Renderizado Recomendados (Hero Concepts)

### A. Orbe Neuronal de Datos (Interactive Data Sphere)
- Malla geométrica de nodos (Icosaedro / Esfera de partículas) conectada por líneas translúcidas cian y violeta (`#00F0FF` / `#7000FF`).
- Partículas flotantes que orbitan suavemente alrededor del núcleo y responden al cursor.

### B. Malla FinTech 3D (Dynamic Data Grid)
- Plano ondulante 3D con altura de vértices modulada por ondas sinusoidales.
- Puntos de datos brillantes simulando flujos de información financiera en tiempo real.

---

## 💻 3. Fragmento de Estructura Canónica

```javascript
// hero-3d.js canonical structure
class Hero3DEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.init();
  }

  init() {
    // Setup Scene, Camera, Renderer (alpha: true, antialias: true)
    // Setup Geometry, Points, Particle System
    // Setup Mouse Listener with Lerp
    // Setup IntersectionObserver for visibility toggle
    // Start RAF loop
  }

  render() {
    if (!this.isVisible) return;
    // Update rotations, uniforms, camera lerp
    // renderer.render(scene, camera)
    requestAnimationFrame(() => this.render());
  }
}
```
