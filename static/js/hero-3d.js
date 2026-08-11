/**
 * NovumWorld 3D Interactive Hero Canvas Engine
 * Multi-Thematic 3D Particle Generator (IA, Crypto, Fitness, Youtube, Viral, Funds)
 * 60 FPS - Zero Dependency - Core Web Vitals & SEO Optimized
 */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', function () {
        const canvas = document.getElementById('hero-3d-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = (canvas.width = canvas.offsetWidth || window.innerWidth);
        let height = (canvas.height = canvas.offsetHeight || 420);

        // Detect theme mode from data attribute or body class
        let theme = (canvas.getAttribute('data-theme') || '').toLowerCase();
        if (!theme) {
            const bodyClass = document.body.className || '';
            const match = bodyClass.match(/theme-([a-z0-9_-]+)/);
            if (match) theme = match[1];
        }

        let mouseX = 0;
        let mouseY = 0;
        let targetMouseX = 0;
        let targetMouseY = 0;

        let isVisible = true;
        let animationFrameId = null;

        // Particle configuration based on Theme
        const particles = [];
        const PARTICLE_COUNT = Math.min(130, Math.max(70, Math.floor(width / 10)));
        const SPHERE_RADIUS = Math.min(width, height) * 0.35;

        function initParticles() {
            particles.length = 0;

            if (theme === 'crypto') {
                // THEME CRYPTO: Matrix Blockchain Grid & Gold/Emerald Node Lattice
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const row = Math.floor(i / 10);
                    const col = i % 10;
                    particles.push({
                        x3d: (col - 5) * 55,
                        y3d: (row - 5) * 35,
                        z3d: (Math.random() - 0.5) * 160,
                        size: Math.random() * 2.5 + 1.5,
                        color: i % 5 === 0 ? '#FFD700' : (i % 2 === 0 ? '#00FF41' : '#00F0FF'),
                        speed: Math.random() * 0.02 + 0.005,
                        phase: Math.random() * Math.PI * 2
                    });
                }
            } else if (theme === 'fitness' || theme === 'biohacking') {
                // THEME FITNESS: 3D DNA Double Helix & Kinetic Waves
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const strand = i % 2 === 0 ? 1 : -1;
                    const angle = (i / PARTICLE_COUNT) * Math.PI * 8;
                    const y = (i / PARTICLE_COUNT - 0.5) * SPHERE_RADIUS * 2.2;
                    particles.push({
                        x3d: Math.cos(angle + (strand * Math.PI)) * 90,
                        y3d: y,
                        z3d: Math.sin(angle + (strand * Math.PI)) * 90,
                        strand: strand,
                        size: Math.random() * 2 + 2,
                        color: strand === 1 ? '#FF5F1F' : '#FF0055',
                        speed: 0.015
                    });
                }
            } else if (theme === 'youtube' || theme === 'creators') {
                // THEME CREATORS / YOUTUBE: Audio Equalizer Wave & Radial Aura
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const angle = (i / PARTICLE_COUNT) * Math.PI * 2;
                    const radius = SPHERE_RADIUS * (0.6 + 0.4 * Math.sin(i * 3));
                    particles.push({
                        x3d: Math.cos(angle) * radius,
                        y3d: Math.sin(angle) * radius,
                        z3d: (Math.random() - 0.5) * 120,
                        size: Math.random() * 2.5 + 1.5,
                        color: i % 3 === 0 ? '#FF3333' : (i % 2 === 0 ? '#FF007A' : '#FFD700'),
                        angle: angle,
                        baseRadius: radius,
                        freq: i % 8 + 1
                    });
                }
            } else if (theme === 'viral') {
                // THEME VIRAL: Swirling Quantum Vortex & Starburst Particles
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const arm = i % 4;
                    const dist = (i / PARTICLE_COUNT) * SPHERE_RADIUS * 1.2;
                    const angle = (dist * 0.03) + (arm * Math.PI / 2);
                    particles.push({
                        x3d: Math.cos(angle) * dist,
                        y3d: (Math.random() - 0.5) * 80,
                        z3d: Math.sin(angle) * dist,
                        dist: dist,
                        angle: angle,
                        size: Math.random() * 2.2 + 1.5,
                        color: i % 3 === 0 ? '#A855F7' : (i % 2 === 0 ? '#00F0FF' : '#FF007A')
                    });
                }
            } else if (theme === 'funds' || theme === 'realestate') {
                // THEME FUNDS / FINANCE: Candlestick Vectors & Market Growth Constellation
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const col = (i / PARTICLE_COUNT - 0.5) * width * 0.7;
                    const baseHeight = Math.sin(i * 0.3) * 80;
                    particles.push({
                        x3d: col,
                        y3d: baseHeight + (Math.random() - 0.5) * 40,
                        z3d: (Math.random() - 0.5) * 140,
                        size: Math.random() * 2.5 + 1.5,
                        color: i % 4 === 0 ? '#F59E0B' : (i % 2 === 0 ? '#10B981' : '#00F0FF')
                    });
                }
            } else {
                // DEFAULT / IA / SAAS: Cyberpunk Neural Data Orb
                for (let i = 0; i < PARTICLE_COUNT; i++) {
                    const phi = Math.acos(-1 + (2 * i) / PARTICLE_COUNT);
                    const theta = Math.sqrt(PARTICLE_COUNT * Math.PI) * phi;
                    particles.push({
                        x3d: SPHERE_RADIUS * Math.cos(theta) * Math.sin(phi),
                        y3d: SPHERE_RADIUS * Math.sin(theta) * Math.sin(phi),
                        z3d: SPHERE_RADIUS * Math.cos(phi),
                        size: Math.random() * 2 + 1.5,
                        color: i % 4 === 0 ? '#7000FF' : (i % 3 === 0 ? '#FF007A' : '#00F0FF')
                    });
                }
            }
        }

        initParticles();

        // Mouse Parallax Track
        window.addEventListener('mousemove', function (e) {
            const rect = canvas.getBoundingClientRect();
            if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
                targetMouseX = (e.clientX - rect.left - width / 2) * 0.0008;
                targetMouseY = (e.clientY - rect.top - height / 2) * 0.0008;
            }
        });

        // Resize Event
        window.addEventListener('resize', function () {
            width = canvas.width = canvas.offsetWidth || window.innerWidth;
            height = canvas.height = canvas.offsetHeight || 420;
            initParticles();
        });

        // IntersectionObserver for 60 FPS performance toggle
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(function (entries) {
                entries.forEach(entry => {
                    isVisible = entry.isIntersecting;
                    if (isVisible && !animationFrameId) {
                        loop();
                    }
                });
            }, { threshold: 0.05 });
            observer.observe(canvas);
        }

        let rotationX = 0;
        let rotationY = 0;
        let time = 0;

        function render() {
            ctx.clearRect(0, 0, width, height);
            time += 0.02;

            // Interpolation for smooth cursor response
            mouseX += (targetMouseX - mouseX) * 0.05;
            mouseY += (targetMouseY - mouseY) * 0.05;

            rotationY += 0.003 + mouseX;
            rotationX += 0.001 + mouseY;

            const cx = width / 2;
            const cy = height / 2;
            const projected = [];

            const cosX = Math.cos(rotationX);
            const sinX = Math.sin(rotationX);
            const cosY = Math.cos(rotationY);
            const sinY = Math.sin(rotationY);

            // Dynamic Motion Math per Theme
            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                let px = p.x3d;
                let py = p.y3d;
                let pz = p.z3d;

                if (theme === 'crypto') {
                    pz += Math.sin(time + p.phase) * 15;
                } else if (theme === 'fitness' || theme === 'biohacking') {
                    const angle = (i / PARTICLE_COUNT) * Math.PI * 8 + time * 1.5;
                    px = Math.cos(angle + (p.strand * Math.PI)) * 90;
                    pz = Math.sin(angle + (p.strand * Math.PI)) * 90;
                } else if (theme === 'youtube' || theme === 'creators') {
                    const radius = p.baseRadius + Math.sin(time * p.freq) * 20;
                    px = Math.cos(p.angle + time * 0.2) * radius;
                    py = Math.sin(p.angle + time * 0.2) * radius;
                } else if (theme === 'viral') {
                    const angle = p.angle + time * 0.5;
                    px = Math.cos(angle) * p.dist;
                    pz = Math.sin(angle) * p.dist;
                } else if (theme === 'funds' || theme === 'realestate') {
                    py += Math.sin(time + i * 0.2) * 8;
                }

                // Y & X Rotation
                let x1 = px * cosY - pz * sinY;
                let z1 = pz * cosY + px * sinY;
                let y1 = py * cosX - z1 * sinX;
                let z2 = z1 * cosX + py * sinX;

                const fov = 380;
                const scale = fov / (fov + z2);
                const x2d = cx + x1 * scale;
                const y2d = cy + y1 * scale;

                projected.push({ x: x2d, y: y2d, scale: scale, z: z2, color: p.color, size: p.size * scale });
            }

            // Sort Depth
            projected.sort((a, b) => b.z - a.z);

            // Connect Synapses / Network Lines
            ctx.lineWidth = 0.5;
            const maxDist = theme === 'crypto' ? 65 : 75;
            for (let i = 0; i < projected.length; i++) {
                for (let j = i + 1; j < projected.length; j++) {
                    const dx = projected[i].x - projected[j].x;
                    const dy = projected[i].y - projected[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < maxDist) {
                        const alpha = (1 - dist / maxDist) * 0.22 * Math.min(projected[i].scale, projected[j].scale);
                        const lineHue = theme === 'crypto' ? '0, 255, 65' : (theme === 'youtube' ? '255, 51, 51' : '0, 240, 255');
                        ctx.strokeStyle = `rgba(${lineHue}, ${alpha})`;
                        ctx.beginPath();
                        ctx.moveTo(projected[i].x, projected[i].y);
                        ctx.lineTo(projected[j].x, projected[j].y);
                        ctx.stroke();
                    }
                }
            }

            // Draw Nodes
            for (let i = 0; i < projected.length; i++) {
                const p = projected[i];
                const alpha = Math.max(0.15, Math.min(1, p.scale));

                ctx.save();
                ctx.fillStyle = p.color;
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.arc(p.x, p.y, Math.max(0.6, p.size), 0, Math.PI * 2);
                ctx.fill();

                if (p.z < 0) {
                    ctx.strokeStyle = p.color;
                    ctx.lineWidth = 0.8;
                    ctx.globalAlpha = alpha * 0.35;
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.size * 2.2, 0, Math.PI * 2);
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
