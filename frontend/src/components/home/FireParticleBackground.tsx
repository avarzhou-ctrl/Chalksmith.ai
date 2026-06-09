'use client';

import { useEffect, useRef } from 'react';

type Particle = {
  baseX: number;
  baseY: number;
  drift: number;
  phase: number;
  amplitude: number;
  size: number;
  opacity: number;
};

export default function FireParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const particles: Particle[] = [];

    let animationFrame = 0;
    let width = 0;
    let height = 0;
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

    const seedParticles = () => {
      particles.length = 0;

      const columnCount = Math.ceil(width / (width < 768 ? 34 : 28));
      const rowCount: number = width < 768 ? 7 : 10;
      const verticalPadding = height * 0.12;
      const bandHeight = Math.max(1, height - verticalPadding * 2);

      for (let row = 0; row < rowCount; row += 1) {
        const rowProgress = rowCount === 1 ? 0 : row / (rowCount - 1);
        const baseY = verticalPadding + bandHeight * rowProgress;

        for (let column = 0; column < columnCount; column += 1) {
          particles.push({
            baseX: (column / columnCount) * width + (Math.random() - 0.5) * 12,
            baseY: baseY + (Math.random() - 0.5) * 28,
            drift: 5 + Math.random() * 10,
            phase: Math.random() * Math.PI * 2,
            amplitude: 10 + Math.random() * 22,
            size: 0.9 + Math.random() * 1.8,
            opacity: 0.12 + Math.random() * 0.22,
          });
        }
      }
    };

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * pixelRatio);
      canvas.height = Math.floor(height * pixelRatio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      seedParticles();

      if (prefersReducedMotion) {
        draw();
      }
    };

    const draw = (time = 0) => {
      const seconds = time / 1000;

      context.clearRect(0, 0, width, height);
      context.fillStyle = 'rgba(12, 10, 9, 0.34)';
      context.fillRect(0, 0, width, height);

      for (const particle of particles) {
        const wrapWidth = width + 80;
        const x = ((particle.baseX + seconds * particle.drift) % wrapWidth) - 40;
        const wave = Math.sin(x * 0.018 + particle.phase + seconds * 0.28);
        const secondaryWave = Math.cos(x * 0.008 + particle.phase * 0.7 + seconds * 0.12);
        const y = particle.baseY + wave * particle.amplitude + secondaryWave * 6;
        const pulse = 0.75 + Math.sin(seconds * 0.42 + particle.phase) * 0.25;

        context.beginPath();
        context.fillStyle = `rgba(217, 119, 6, ${particle.opacity * pulse})`;
        context.shadowColor = `rgba(217, 119, 6, ${particle.opacity * 0.9})`;
        context.shadowBlur = 8;
        context.arc(x, y, particle.size, 0, Math.PI * 2);
        context.fill();
        context.shadowBlur = 0;
      }

      if (!prefersReducedMotion) {
        animationFrame = window.requestAnimationFrame(draw);
      }
    };

    resize();
    draw();

    window.addEventListener('resize', resize);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="fixed inset-0 z-0 h-full w-full bg-primary-bg"
    />
  );
}
