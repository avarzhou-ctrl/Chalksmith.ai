'use client';

import React, { useState, useRef, useEffect } from 'react';

interface VideoComparisonProps {
  beforeSrc: string;
  afterSrc: string;
}

export default function VideoComparison({ beforeSrc, afterSrc }: VideoComparisonProps) {
  const [sliderPos, setSliderPos] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const videoBeforeRef = useRef<HTMLVideoElement>(null);
  const videoAfterRef = useRef<HTMLVideoElement>(null);

  const handleMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX : (e as React.MouseEvent).clientX;
    const position = ((x - rect.left) / rect.width) * 100;
    
    setSliderPos(Math.max(0, Math.min(100, position)));
  };

  // Synchronize video playback
  useEffect(() => {
    const v1 = videoBeforeRef.current;
    const v2 = videoAfterRef.current;
    if (!v1 || !v2) return;

    const syncPlayback = () => {
      if (Math.abs(v1.currentTime - v2.currentTime) > 0.1) {
        v2.currentTime = v1.currentTime;
      }
    };

    v1.addEventListener('timeupdate', syncPlayback);
    return () => v1.removeEventListener('timeupdate', syncPlayback);
  }, []);

  return (
    <div 
      ref={containerRef}
      className="relative w-full aspect-video overflow-hidden rounded-lg border border-stone-700 bg-black cursor-ew-resize select-none"
      onMouseMove={handleMove}
      onTouchMove={handleMove}
    >
      {/* "After" Video (Background) */}
      <video
        ref={videoAfterRef}
        src={afterSrc}
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* "Before" Video (Overlay) */}
      <div 
        className="absolute inset-0 w-full h-full overflow-hidden"
        style={{ width: `${sliderPos}%` }}
      >
        <video
          ref={videoBeforeRef}
          src={beforeSrc}
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 h-full object-cover"
          style={{ width: `${100 / (sliderPos / 100)}%`, maxWidth: 'none' }}
        />
      </div>

      {/* Slider Line & Handle */}
      <div 
        className="absolute inset-y-0 w-0.5 bg-accent shadow-[0_0_10px_rgba(217,119,6,0.5)] z-10"
        style={{ left: `${sliderPos}%` }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-accent rounded-full flex items-center justify-center shadow-lg border-2 border-white/20">
          <div className="flex gap-1">
            <div className="w-0.5 h-3 bg-white/60 rounded-full" />
            <div className="w-0.5 h-3 bg-white/60 rounded-full" />
          </div>
        </div>
      </div>

      {/* Labels */}
      <div className="absolute bottom-4 left-4 z-20 px-2 py-1 bg-black/50 backdrop-blur-md rounded text-[10px] font-bold text-white uppercase tracking-wider border border-white/10 pointer-events-none">
        Code
      </div>
      <div className="absolute bottom-4 right-4 z-20 px-2 py-1 bg-accent/80 backdrop-blur-md rounded text-[10px] font-bold text-white uppercase tracking-wider border border-white/10 pointer-events-none">
        Product
      </div>
    </div>
  );
}
