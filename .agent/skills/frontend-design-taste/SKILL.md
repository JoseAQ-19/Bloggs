---
name: frontend-design-taste
description: Reglas y estándares de diseño frontend de alto criterio (Taste / Anti-AI-Slop) para NovumWorld. Define tipografías finas, paleta de color modo oscuro cyberpunk/tech minimalist, glassmorphic de alta fidelidad, espaciado visual y microinteracciones.
---

# 🎨 Skill: Frontend Design Taste & Anti-AI-Slop Standard

Esta habilidad establece las reglas obligatorias de diseño UI/UX de vanguardia para eliminar el aspecto de "diseño genérico de IA" (*AI Slop*) en la web **novumworld.com** y reemplazarlo con una estética hiperprofesional, cinematográfica y moderna orientada al periodismo de datos y la inteligencia artificial.

---

## 🚫 1. Prohibiciones Anti-AI-Slop (Anti-Slop Directives)
1. **NO usar gradientes violeta-azul genéricos de Tailwind/Bootstrap por defecto.**
2. **NO usar tarjetas blancas planas de 3 columnas repetitivas sin profundidad.**
3. **NO usar sombras pesadas difuminadas opacas.** Usar resplandores translúcidos (`box-shadow: 0 0 25px rgba(0, 240, 255, 0.12)`).
4. **NO usar tipografías por defecto del sistema.** Usar pares tipográficos cinematográficos importados explícitamente desde Google Fonts.
5. **NO usar bordes sólidos gruesos de 1px solido gris.** Usar bordes translúcidos de cristal (`border: 1px solid rgba(255, 255, 255, 0.08)`).

---

## 💎 2. Sistema de Diseño Visual (Design Tokens)

### 🎨 Paleta de Colores (Cyberpunk / High-Tech Data Journalism)
- **Fondo Primario (`--bg-primary`)**: `#07090E` (Negro abisal profundo)
- **Fondo Secundario / Tarjetas (`--bg-card`)**: `rgba(15, 23, 42, 0.65)` (Azul noche translúcido)
- **Superficie de Cristal (`--bg-glass`)**: `rgba(22, 27, 46, 0.5)` con `backdrop-filter: blur(16px)`
- **Acento Cian Neón (`--accent-cyan`)**: `#00F0FF` (Periodismo de datos & IA)
- **Acento Violeta Electrico (`--accent-purple`)**: `#7000FF` (Señales de mercado & Crypto)
- **Acento Esmeralda (`--accent-emerald`)**: `#10B981` (Métricas & Crecimiento)
- **Texto Principal (`--text-main`)**: `#F8FAFC` (Blanco impoluto)
- **Texto Secundario (`--text-muted`)**: `#94A3B8` (Gris frío legible)

### ✒️ Pares Tipográficos (Cinematic Typography)
- **Titulares (`h1`, `h2`, `h3`, Hero Titles)**: `Syne`, sans-serif (700/800 ExtraBold) o `Space Grotesk`, sans-serif.
- **Cuerpo de texto & Párrafos**: `Plus Jakarta Sans`, sans-serif o `Inter`, sans-serif (400 Regular / 500 Medium).
- **Métricas & Datos Cuantitativos**: `JetBrains Mono` / `Space Grotesk`.

### ✨ Glassmorphism & Depth Tokens
```css
.glass-panel {
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.glass-card-hover {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.glass-card-hover:hover {
  transform: translateY(-4px);
  border-color: rgba(0, 240, 255, 0.4);
  box-shadow: 0 12px 40px rgba(0, 240, 255, 0.15), 0 0 0 1px rgba(0, 240, 255, 0.2);
}
```

---

## ⚡ 3. Microinteracciones y Animaciones

- **Transiciones**: Usar siempre curvas `cubic-bezier(0.16, 1, 0.3, 1)` para respuestas táctiles suaves e instantáneas.
- **Efecto Glow**: Los elementos interactivos (botones, badges, tarjetas destacadas) deben emitir un *glow* sutil cian/violeta al pasar el cursor.
- **Badges y Pulse**: Indicadores en vivo (ej. "LIVE DATA") deben contar con un punto parpadeante con animación `@keyframes pulse-glow`.

---

## 🛡️ 4. Cumplimiento AdSense & UX (AdSense Safe Directives)
- Asegurar contraste superior a 4.5:1 (WCAG AA) en todos los textos de tarjetas y lecturas.
- Dejar márgenes claros alrededor de las zonas de contenido para evitar superposiciones con anuncios o navegación.
