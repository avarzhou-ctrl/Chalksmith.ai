'use client';

import { useEffect, useRef } from 'react';

type WaveDot = {
  baseX: number;
  baseY: number;
  row: number;
  column: number;
  phase: number;
  isAmber: boolean;
};

export default function ChalkDust() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    const drawingCanvas: HTMLCanvasElement = canvas;
    const drawingContext: CanvasRenderingContext2D = context;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let frameId = 0;
    let lastFrame = 0;
    let dots: WaveDot[] = [];

    function resize() {
      const bounds = drawingCanvas.getBoundingClientRect();
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
      drawingCanvas.width = Math.max(1, Math.floor(bounds.width * pixelRatio));
      drawingCanvas.height = Math.max(1, Math.floor(bounds.height * pixelRatio));
      drawingContext.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);

      const spacing = bounds.width < 640 ? 24 : 22;
      const columns = Math.ceil(bounds.width / spacing) + 2;
      const rows = Math.ceil(bounds.height / spacing) + 2;

      dots = Array.from({ length: columns * rows }, (_, index) => {
        const row = Math.floor(index / columns);
        const column = index % columns;

        return {
          baseX: (column - 1) * spacing,
          baseY: (row - 1) * spacing,
          row,
          column,
          phase: row * 0.38 + column * 0.025,
          isAmber: (row * 7 + column * 11) % 29 === 0,
        };
      });
    }

    function draw(timestamp: number) {
      const bounds = drawingCanvas.getBoundingClientRect();
      drawingContext.clearRect(0, 0, bounds.width, bounds.height);

      const time = reducedMotion.matches ? 0 : timestamp * 0.0005;
      const verticalCenter = bounds.height / 2;

      dots.forEach((dot) => {
        const edgeDistance = Math.min(
          dot.baseX,
          bounds.width - dot.baseX,
          dot.baseY,
          bounds.height - dot.baseY,
        );
        const edgeFade = Math.max(0, Math.min(1, edgeDistance / 72));
        const verticalDistance = Math.abs(dot.baseY - verticalCenter) / Math.max(verticalCenter, 1);
        const waveEnvelope = Math.max(0.4, 1 - verticalDistance * 0.5);
        const primaryWave = Math.sin(dot.baseX * 0.015 + time * 2.35 + dot.phase);
        const secondaryWave = Math.sin(dot.baseX * 0.007 - time * 1.25 + dot.row * 0.18) * 0.42;
        const waveStrength = primaryWave + secondaryWave;
        const brightness = (primaryWave + 1) / 2;
        const waveY = waveStrength * 28 * waveEnvelope;
        const waveX = Math.sin(time * 0.9 + dot.row * 0.24) * 4;
        const opacity = (0.1 + brightness * 0.26) * edgeFade * (0.65 + waveEnvelope * 0.35);
        const radius = (dot.isAmber ? 1.65 : 1.05) + brightness * 0.55;

        drawingContext.beginPath();
        drawingContext.fillStyle = dot.isAmber
          ? `rgba(245, 158, 11, ${Math.min(opacity * 1.55, 0.75)})`
          : `rgba(214, 211, 209, ${opacity})`;
        drawingContext.arc(dot.baseX + waveX, dot.baseY + waveY, radius, 0, Math.PI * 2);
        drawingContext.fill();
      });
    }

    function animate(timestamp: number) {
      if (timestamp - lastFrame > 50) {
        draw(timestamp);
        lastFrame = timestamp;
      }
      frameId = window.requestAnimationFrame(animate);
    }

    function updateMotionPreference() {
      window.cancelAnimationFrame(frameId);
      if (reducedMotion.matches) {
        draw(0);
      } else {
        frameId = window.requestAnimationFrame(animate);
      }
    }

    const observer = new ResizeObserver(() => {
      resize();
      draw(0);
    });

    observer.observe(drawingCanvas);
    resize();
    // Paint once immediately because mobile browsers can defer the first animation frame.
    draw(0);
    updateMotionPreference();
    reducedMotion.addEventListener?.('change', updateMotionPreference);

    return () => {
      observer.disconnect();
      reducedMotion.removeEventListener?.('change', updateMotionPreference);
      window.cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 h-screen w-screen [mask-image:radial-gradient(ellipse_at_center,black_55%,transparent_100%)] [-webkit-mask-image:radial-gradient(ellipse_at_center,black_55%,transparent_100%)] sm:[mask-image:radial-gradient(ellipse_at_center,black_35%,transparent_100%)] sm:[-webkit-mask-image:radial-gradient(ellipse_at_center,black_35%,transparent_100%)]"
    />
  );
}
