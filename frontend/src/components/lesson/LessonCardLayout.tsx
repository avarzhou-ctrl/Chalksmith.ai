import type { DragEventHandler, ReactNode } from 'react';

import LessonFormatIcon from '@/components/lesson/LessonFormatIcon';
import type { LessonFormat } from '@/lib/types/api';

interface LessonCardLayoutProps {
  format: LessonFormat;
  title: ReactNode;
  subtitle?: ReactNode;
  subtitleInteractive?: boolean;
  description?: ReactNode;
  tags: string[];
  overlay?: ReactNode;
  headerAction?: ReactNode;
  statusMessage?: ReactNode;
  footer?: ReactNode;
  footerInteractive?: boolean;
  draggable?: boolean;
  onDragStart?: DragEventHandler<HTMLElement>;
  onDragEnd?: DragEventHandler<HTMLElement>;
  children?: ReactNode;
}

export default function LessonCardLayout({
  format,
  title,
  subtitle,
  subtitleInteractive = false,
  description,
  tags,
  overlay,
  headerAction,
  statusMessage,
  footer,
  footerInteractive = false,
  draggable = false,
  onDragStart,
  onDragEnd,
  children,
}: LessonCardLayoutProps) {
  return (
    <article
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={`relative flex min-h-64 flex-col rounded-2xl border border-border bg-secondary-bg p-5 shadow-lg shadow-stone-950/20 ${draggable ? 'cursor-grab active:cursor-grabbing' : ''}`}
    >
      {overlay}
      <header className="pointer-events-none relative z-20 flex items-start gap-3">
        <LessonFormatIcon format={format} />
        <section className="min-w-0 flex-1">
          <h2 className="line-clamp-2 text-xl font-semibold leading-snug text-primary-text">
            {title}
          </h2>
          <div className={`${subtitleInteractive ? 'pointer-events-auto' : 'pointer-events-none'} mt-1 min-h-5 text-sm text-secondary-text`}>
            {subtitle}
          </div>
        </section>
        {headerAction && <div className="pointer-events-auto shrink-0">{headerAction}</div>}
      </header>

      <div className="pointer-events-none relative z-10 mt-4 min-h-12 line-clamp-3 text-sm leading-6 text-secondary-text">
        {description || <span className="italic text-secondary-text/70">No description yet.</span>}
      </div>

      {tags.length > 0 && (
        <section className="pointer-events-none relative z-10 mt-4 flex flex-wrap gap-1.5" aria-label="Lesson tags">
          {tags.slice(0, 3).map((tag) => (
            <span key={tag.toLocaleLowerCase()} className="rounded-full bg-accent/10 px-2.5 py-1 text-xs text-accent">
              {tag}
            </span>
          ))}
          {tags.length > 3 && (
            <span className="px-1 py-1 text-xs text-secondary-text">+{tags.length - 3}</span>
          )}
        </section>
      )}

      {statusMessage && (
        <div className="pointer-events-none relative z-10 mt-3">{statusMessage}</div>
      )}

      {footer && (
        <footer className={`${footerInteractive ? 'pointer-events-auto' : 'pointer-events-none'} relative z-10 mt-auto pt-6`}>
          {footer}
        </footer>
      )}
      {children}
    </article>
  );
}
