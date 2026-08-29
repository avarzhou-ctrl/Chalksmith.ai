'use client';

import { useEffect, useRef, useState } from 'react';

const statistics = [
  { value: 5, suffix: 'hours', label: 'per week collecting resources.' },
  { value: 7, suffix: 'hours', label: 'per week building from scratch.' },
  { value: 12, suffix: 'hours', label: 'per week lost managing lessons.' },
];

function AnimatedNumber({ value, start }: { value: number; start: boolean }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (!start) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplayValue(value);
      return;
    }

    const duration = 900;
    const startedAt = performance.now();
    let frameId = 0;

    function update(timestamp: number) {
      const progress = Math.min((timestamp - startedAt) / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(value * easedProgress));
      if (progress < 1) frameId = window.requestAnimationFrame(update);
    }

    frameId = window.requestAnimationFrame(update);
    return () => window.cancelAnimationFrame(frameId);
  }, [start, value]);

  return <>{displayValue}</>;
}

export default function EducatorEquation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hasEntered, setHasEntered] = useState(false);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    // A mobile reload can restore the page below this section before the observer starts.
    if (element.getBoundingClientRect().top <= window.innerHeight * 0.9) {
      setHasEntered(true);
      return;
    }

    if (!('IntersectionObserver' in window)) {
      setHasEntered(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setHasEntered(true);
          observer.disconnect();
        }
      },
      // The cards stack on phones, so waiting for 35% of the whole grid can miss the viewport.
      { rootMargin: '0px 0px -10% 0px', threshold: 0.01 },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="mt-10 grid gap-4 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-stretch">
      {statistics.map((statistic, index) => (
        <div key={statistic.value} className="contents">
          <article className="group relative overflow-hidden rounded-2xl border border-stone-700/80 bg-secondary-bg p-6 text-center shadow-xl shadow-black/15 transition-colors duration-300 hover:border-amber-600/50">
            <span aria-hidden="true" className="absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/70 to-transparent" />
            <p className="text-4xl font-bold tracking-tight text-accent sm:text-5xl">
              <AnimatedNumber value={statistic.value} start={hasEntered} />{' '}
              <span className="text-2xl">{statistic.suffix}</span>
            </p>
            <p className="mx-auto mt-3 max-w-48 text-base leading-6 text-primary-text">{statistic.label}</p>
          </article>
          {index < statistics.length - 1 && (
            <p
              aria-hidden="true"
              className={`grid place-items-center text-4xl font-light text-amber-300 transition-all duration-500 motion-reduce:transition-none ${
                hasEntered ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'
              } ${index === 0 ? 'delay-300' : 'delay-700'}`}
            >
              {index === 0 ? '+' : '='}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
