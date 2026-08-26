import { Search, Video } from 'lucide-react';

import PublishedLessonGrid from '@/components/content/PublishedLessonGrid';

export default function Content() {
  return (
    <main className="min-h-screen bg-primary-bg px-6 py-16 font-sans text-primary-text sm:px-10 lg:px-16">
      <section className="mx-auto w-full max-w-7xl">
        <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <section className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Explore</p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-5xl">Explore lessons</h1>
            <p className="mt-4 text-base leading-7 text-secondary-text">
              Discover lessons published by the Chalksmith community. Anyone can view and download them, while only the original author can continue editing.
            </p>
          </section>
          <a
            href="https://www.youtube.com/@SquishBJ"
            target="_blank"
            rel="noreferrer"
            className="flex w-fit items-center gap-2 rounded-xl border border-border px-4 py-2 text-sm font-medium text-secondary-text transition-colors hover:border-accent hover:text-accent"
          >
            <Video size={18} />
            Visit YouTube
          </a>
        </header>

        <section className="my-8 flex items-center gap-3 rounded-2xl border border-border bg-secondary-bg px-4 py-3">
          <Search size={20} className="shrink-0 text-secondary-text" />
          <input
            type="search"
            readOnly
            aria-label="Search published lessons"
            placeholder="Search lessons"
            className="min-w-0 flex-1 bg-transparent text-sm text-primary-text outline-none placeholder:text-secondary-text"
          />
          <span className="hidden rounded-lg bg-surface px-3 py-1 text-xs text-secondary-text sm:block">Coming soon</span>
        </section>

        <PublishedLessonGrid />
      </section>
    </main>
  );
}
