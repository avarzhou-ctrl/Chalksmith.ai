'use client';

import { useEffect, useRef } from 'react';

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  life: number;
  maxLife: number;
  hue: number;
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
    const pointer = {
      x: window.innerWidth / 2,
      y: window.innerHeight * 0.72,
      active: false,
    };

    let animationFrame = 0;
    let width = 0;
    let height = 0;
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * pixelRatio);
      canvas.height = Math.floor(height * pixelRatio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    };

    const createParticle = (x: number, y: number, intensity = 1) => {
      const spread = pointer.active ? 16 : 34;
      particles.push({
        x: x + (Math.random() - 0.5) * spread,
        y: y + (Math.random() - 0.5) * 10,
        vx: (Math.random() - 0.5) * 0.7 * intensity,
        vy: -(0.65 + Math.random() * 1.65) * intensity,
        size: 1.4 + Math.random() * 3.6,
        life: 0,
        maxLife: 54 + Math.random() * 56,
        hue: 24 + Math.random() * 28,
      });
    };

    const draw = () => {
      context.clearRect(0, 0, width, height);
      context.fillStyle = 'rgba(12, 10, 9, 0.28)';
      context.fillRect(0, 0, width, height);

      if (!prefersReducedMotion) {
        const baseY = height + 8;
        const baseCount = width < 768 ? 3 : 5;

        for (let index = 0; index < baseCount; index += 1) {
          createParticle(Math.random() * width, baseY, 0.72);
        }

        if (pointer.active) {
          for (let index = 0; index < 4; index += 1) {
            createParticle(pointer.x, pointer.y, 1.12);
          }
        }
      }

      for (let index = particles.length - 1; index >= 0; index -= 1) {
        const particle = particles[index];
        particle.life += 1;
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.vx += (Math.random() - 0.5) * 0.08;
        particle.vy -= 0.006;

        const progress = particle.life / particle.maxLife;
        const opacity = Math.max(0, 1 - progress);
        const radius = particle.size * (1 - progress * 0.45);

        context.beginPath();
        context.fillStyle = `hsla(${particle.hue}, 96%, ${56 + progress * 18}%, ${opacity * 0.42})`;
        context.shadowColor = `hsla(${particle.hue}, 98%, 54%, ${opacity * 0.72})`;
        context.shadowBlur = 14;
        context.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
        context.fill();
        context.shadowBlur = 0;

        if (particle.life >= particle.maxLife || particle.y < -24) {
          particles.splice(index, 1);
        }
      }

      animationFrame = window.requestAnimationFrame(draw);
    };

    const updatePointer = (event: PointerEvent) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
    };

    const releasePointer = () => {
      pointer.active = false;
    };

    resize();
    draw();

    window.addEventListener('resize', resize);
    window.addEventListener('pointermove', updatePointer);
    window.addEventListener('pointerdown', updatePointer);
    window.addEventListener('pointerleave', releasePointer);
    window.addEventListener('blur', releasePointer);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', updatePointer);
      window.removeEventListener('pointerdown', updatePointer);
      window.removeEventListener('pointerleave', releasePointer);
      window.removeEventListener('blur', releasePointer);
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
