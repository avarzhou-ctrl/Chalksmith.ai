'use client';

import { useEffect, useRef, useState, type PointerEvent, type ReactNode } from 'react';

type SparkBurst = {
  id: number;
  x: number;
  y: number;
};

export default function ClickSpark({ children }: { children: ReactNode }) {
  const wrapperRef = useRef<HTMLSpanElement>(null);
  const nextId = useRef(0);
  const cleanupTimers = useRef<number[]>([]);
  const [bursts, setBursts] = useState<SparkBurst[]>([]);

  useEffect(() => () => cleanupTimers.current.forEach(window.clearTimeout), []);

  function createSpark(event: PointerEvent<HTMLSpanElement>) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const bounds = wrapperRef.current?.getBoundingClientRect();
    if (!bounds) return;

    const id = nextId.current++;
    setBursts((current) => [
      ...current,
      { id, x: event.clientX - bounds.left, y: event.clientY - bounds.top },
    ]);

    const timer = window.setTimeout(() => {
      setBursts((current) => current.filter((burst) => burst.id !== id));
    }, 650);
    cleanupTimers.current.push(timer);
  }

  return (
    <span ref={wrapperRef} className="relative inline-flex" onPointerDown={createSpark}>
      {children}
      {bursts.map((burst) => (
        <svg
          key={burst.id}
          viewBox="0 0 64 64"
          aria-hidden="true"
          className="pointer-events-none absolute z-30 size-16 animate-click-spark overflow-visible motion-reduce:hidden"
          style={{ left: burst.x, top: burst.y }}
        >
          <g fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="2.5" className="text-amber-400">
            <path d="M32 11V2" />
            <path d="m47 17 7-7" />
            <path d="M53 32h9" />
            <path d="m47 47 7 7" />
            <path d="M32 53v9" />
            <path d="m17 47-7 7" />
            <path d="M11 32H2" />
            <path d="m17 17-7-7" />
          </g>
        </svg>
      ))}
    </span>
  );
}
