/**
 * NovumWorld 3D Interactive Hero Canvas Engine
 * Cyberpunk Neural Data Orb & Particle Network
 * 60 FPS - Zero Dependency - Core Web Vitals Optimized
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const canvas = document.getElementById('hero-3d-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = (canvas.width = canvas.offsetWidth || window.innerWidth);
        let height = (canvas.height = canvas.offsetHeight || 500);

        let mouseX = 0;
        let mouseY = 0;
        let targetMouseX = 0;
        let targetMouseY = 0;

        let isVisible = true;
        let animationFrameId = null;

        // 3D Sphere Particles
        const PARTICLE_COUNT = Math.min(120, Math.floor(width / 10));
        const SPHERE_RADIUS = Math.min(width, height) * 0.32;
        const particles = [];

        // Generate 3D nodes on sphere surface
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            const phi = Math.acos(-1 + (2 * i) / PARTICLE_COUNT);
            const theta = Math.sqrt(PARTICLE_COUNT * Math.PI) * phi;

            particles.push({
                x3d: SPHERE_RADIUS * Math.cos(theta) * Math.sin(phi),
                y3d: SPHERE_RADIUS * Math.sin(theta) * Math.sin(phi),
                z3d: SPHERE_RADIUS * Math.cos(phi),
                size: Math.random() * 2 + 1.5,
                color: i % 4 === 0 ? '#7000FF' : (i % 3 === 0 ? '#FF007A' : '#00F0FF'),
                pulseSpeed: Math.random() * 0.03 + 0.01,
                pulseOffset: Math.random() * Math.PI * 2
            });
        }

        // Track Mouse with Dampening
        window.addEventListener('mousemove', function (e) {
            const rect = canvas.getBoundingClientRect();
            if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
                targetMouseX = (e.clientX - rect.left - width / 2) * 0.001;
                targetMouseY = (e.clientY - rect.top - height / 2) * 0.001;
            }
        });

        // Resize Listener
        window.addEventListener('resize', function () {
            width = canvas.width = canvas.offsetWidth || window.innerWidth;
            height = canvas.height = canvas.offsetHeight || 500;
        });

        // IntersectionObserver for Performance (Pause offscreen)
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(function (entries) {
                entries.forEach(entry => {
                    isVisible = entry.isIntersecting;
                    if (isVisible && !animationFrameId) {
                        loop();
                    }
                });
            }, { threshold: 0.1 });
            observer.observe(canvas);
        }

        let rotationX = 0;
        let rotationY = 0;

        function render() {
            ctx.clearRect(0, 0, width, height);

            // Smooth Interpolation for Mouse Parallax
            mouseX += (targetMouseX - mouseX) * 0.05;
            mouseY += (targetMouseY - mouseY) * 0.05;

            rotationY += 0.003 + mouseX;
            rotationX += 0.001 + mouseY;

            const cx = width / 2;
            const cy = height / 2;
            const projected = [];

            // Rotate & Project Particles
            const cosX = Math.cos(rotationX);
            const sinX = Math.sin(rotationX);
            const cosY = Math.cos(rotationY);
            const sinY = Math.sin(rotationY);

            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];

                // Y-axis rotation
                let x1 = p.x3d * cosY - p.z3d * sinY;
                let z1 = p.z3d * cosY + p.x3d * sinY;

                // X-axis rotation
                let y1 = p.y3d * cosX - z1 * sinX;
                let z2 = z1 * cosX + p.y3d * sinX;

                // Perspective Projection
                const fov = 400;
                const scale = fov / (fov + z2);
                const x2d = cx + x1 * scale;
                const y2d = cy + y1 * scale;

                projected.push({ x: x2d, y: y2d, scale: scale, z: z2, color: p.color, size: p.size * scale });
            }

            // Sort by Z for Depth Layering
            projected.sort((a, b) => b.z - a.z);

            // Draw Connecting Neural Synapses (Lines)
            ctx.lineWidth = 0.5;
            for (let i = 0; i < projected.length; i++) {
                for (let j = i + 1; j < projected.length; j++) {
                    const dx = projected[i].x - projected[j].x;
                    const dy = projected[i].y - projected[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 75) {
                        const alpha = (1 - dist / 75) * 0.25 * Math.min(projected[i].scale, projected[j].scale);
                        ctx.strokeStyle = `rgba(0, 240, 255, ${alpha})`;
                        ctx.beginPath();
                        ctx.moveTo(projected[i].x, projected[i].y);
                        ctx.lineTo(projected[j].x, projected[j].y);
                        ctx.stroke();
                    }
                }
            }

            // Draw Glowing Nodes
            for (let i = 0; i < projected.length; i++) {
                const p = projected[i];
                const alpha = Math.max(0.15, Math.min(1, p.scale));

                ctx.save();
                ctx.fillStyle = p.color;
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.arc(p.x, p.y, Math.max(0.5, p.size), 0, Math.PI * 2);
                ctx.fill();

                // Glow Ring for Front Nodes
                if (p.z < 0) {
                    ctx.strokeStyle = p.color;
                    ctx.lineWidth = 1;
                    ctx.globalAlpha = alpha * 0.4;
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.size * 2.5, 0, Math.PI * 2);
                    ctx.stroke();
                }
                ctx.restore();
            }
        }

        function loop() {
            if (!isVisible) {
                animationFrameId = null;
                return;
            }
            render();
            animationFrameId = requestAnimationFrame(loop);
        }

        loop();
    });
})();
