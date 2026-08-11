'use client';

import { useState } from 'react';
import { ChevronLeft, ChevronRight, MousePointerClick, Presentation, Video, type LucideIcon } from 'lucide-react';

type ExampleItem = {
  title: string;
  description: string;
  src: string;
  kind: 'video' | 'html';
  icon: LucideIcon;
};

const examples: ExampleItem[] = [
  {
    title: 'Animated STEM video',
    description: 'A concept video that can be played, paused, and reviewed like a classroom clip.',
    src: '/example-video.mp4',
    kind: 'video',
    icon: Video,
  },
  {
    title: 'Interactive display',
    description: 'A exploration where students can adjust variables to manipulate the display.',
    src: '/example-interactive.html',
    kind: 'html',
    icon: MousePointerClick,
  },
  {
    title: 'Traditional slides',
    description: 'A presentation format for step-by-step explanations and classroom discussion.',
    src: '/example-slides.html',
    kind: 'html',
    icon: Presentation,
  },
];

export default function ExamplesCarousel() {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeExample = examples[activeIndex];
  const ActiveIcon = activeExample.icon;

  function showPrevious() {
    setActiveIndex((currentIndex) => (currentIndex === 0 ? examples.length - 1 : currentIndex - 1));
  }

  function showNext() {
    setActiveIndex((currentIndex) => (currentIndex === examples.length - 1 ? 0 : currentIndex + 1));
  }

  return (
    <div className="mt-10 overflow-hidden rounded-lg border border-secondary-bg bg-secondary-bg text-left shadow-2xl shadow-black/30">
      <div className="grid gap-0 lg:grid-cols-[0.82fr_1.18fr]">
        <div className="flex flex-col justify-between border-b border-border p-5 sm:p-6 lg:border-b-0 lg:border-r">
          <div>
            <div className="flex items-center gap-3">
              <span className="grid size-11 place-items-center rounded-lg bg-accent/10 text-accent">
                <ActiveIcon className="size-5" aria-hidden />
              </span>
            </div>
            <h3 className="mt-6 text-2xl font-semibold leading-tight text-primary-text sm:text-3xl">
              {activeExample.title}
            </h3>
            <p className="mt-4 text-sm leading-6 text-secondary-text sm:text-base sm:leading-7">
              {activeExample.description}
            </p>
          </div>

          <div className="mt-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={showPrevious}
                className="grid size-10 place-items-center rounded-lg border border-border text-secondary-text transition-colors hover:border-accent hover:text-accent"
                aria-label="Show previous example"
              >
                <ChevronLeft className="size-5" aria-hidden />
              </button>
              <button
                type="button"
                onClick={showNext}
                className="grid size-10 place-items-center rounded-lg border border-border text-secondary-text transition-colors hover:border-accent hover:text-accent"
                aria-label="Show next example"
              >
                <ChevronRight className="size-5" aria-hidden />
              </button>
            </div>
            <div className="mt-5 flex gap-2" aria-label="Select example">
              {examples.map((example, index) => (
                <button
                  key={example.title}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                  className={`h-2.5 rounded-full transition-all ${
                    index === activeIndex ? 'w-8 bg-accent' : 'w-2.5 bg-stone-600 hover:bg-stone-400'
                  }`}
                  aria-label={`Show ${example.title}`}
                  aria-current={index === activeIndex ? 'true' : undefined}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="bg-primary-bg p-3 sm:p-4">
          <div className="aspect-video overflow-hidden rounded-lg border border-border bg-stone-950">
            {activeExample.kind === 'video' ? (
              <video
                key={activeExample.src}
                src={activeExample.src}
                controls
                playsInline
                className="h-full w-full bg-stone-950 object-contain"
              />
            ) : (
              <iframe
                key={activeExample.src}
                src={activeExample.src}
                title={activeExample.title}
                className="h-full w-full bg-stone-950"
                loading="lazy"
                sandbox="allow-scripts"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
