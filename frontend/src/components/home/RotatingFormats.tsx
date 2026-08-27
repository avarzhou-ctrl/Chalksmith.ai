'use client';

import { useEffect, useState } from 'react';
import { MousePointerClick, Presentation, Video, type LucideIcon } from 'lucide-react';

const formats: Array<{ label: string; icon: LucideIcon }> = [
  { label: 'videos', icon: Video },
  { label: 'interactives', icon: MousePointerClick },
  { label: 'slides', icon: Presentation },
];

export default function RotatingFormats() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reducedMotion.matches) return;

    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % formats.length);
    }, 2200);

    return () => window.clearInterval(interval);
  }, []);

  const activeFormat = formats[activeIndex];
  const ActiveIcon = activeFormat.icon;

  return (
    <p className="mt-5 flex items-center justify-center gap-2 text-sm font-medium text-stone-300" aria-label="One source. Three outcomes: videos, interactives, and slides.">
      <span>One source. Three outcomes:</span>
      <span className="inline-flex min-w-28 items-center gap-1.5 text-left text-amber-400 sm:min-w-32" aria-hidden="true">
        <ActiveIcon key={`${activeFormat.label}-icon`} className="size-4 animate-format-in motion-reduce:animate-none" />
        <span key={activeFormat.label} className="animate-format-in motion-reduce:animate-none">
          {activeFormat.label}
        </span>
      </span>
    </p>
  );
}
