import type { ReactNode } from 'react';

interface LessonViewportProps {
  children: ReactNode;
}

export default function LessonViewport({ children }: LessonViewportProps) {
  return (
    <section className="flex size-full min-h-0 min-w-0 items-center justify-center overflow-hidden bg-stone-950">
      <section className="relative aspect-video h-full max-h-full w-auto max-w-full overflow-hidden bg-stone-950">
        {children}
      </section>
    </section>
  );
}
