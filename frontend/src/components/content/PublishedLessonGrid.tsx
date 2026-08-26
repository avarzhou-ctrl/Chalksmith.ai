'use client';

import { Download, ExternalLink } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import LessonFormatIcon from '@/components/dashboard/LessonFormatIcon';
import Button from '@/components/ui/Button';
import { createPublicApiClient } from '@/lib/api/client';
import { getPublishedLessonAccessUrl, listPublishedLessons } from '@/lib/api/explore';
import type { PublishedLessonItem } from '@/lib/types/api';

export default function PublishedLessonGrid() {
  const api = useMemo(() => createPublicApiClient(), []);
  const [lessons, setLessons] = useState<PublishedLessonItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listPublishedLessons(api, controller.signal)
      .then(setLessons)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load published lessons.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api]);

  async function viewLesson(lessonId: string) {
    const pendingWindow = window.open('about:blank', '_blank');
    setActiveAction(`view:${lessonId}`);
    setError(null);
    try {
      const access = await getPublishedLessonAccessUrl(api, lessonId);
      if (pendingWindow) {
        pendingWindow.opener = null;
        pendingWindow.location.href = access.url;
      } else {
        window.location.assign(access.url);
      }
    } catch (caught) {
      pendingWindow?.close();
      setError(caught instanceof Error ? caught.message : 'Failed to open this lesson.');
    } finally {
      setActiveAction(null);
    }
  }

  async function downloadLesson(lessonId: string) {
    setActiveAction(`download:${lessonId}`);
    setError(null);
    try {
      const access = await getPublishedLessonAccessUrl(api, lessonId, true);
      window.location.assign(access.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to download this lesson.');
    } finally {
      setActiveAction(null);
    }
  }

  if (isLoading) {
    return <p className="rounded-xl border border-border bg-surface/20 p-6 text-secondary-text">Loading published lessons…</p>;
  }

  return (
    <section aria-label="Published lessons">
      {error && (
        <p className="mb-5 rounded-xl border border-red-900/60 bg-red-950/30 p-4 text-sm text-red-200">
          {error}
        </p>
      )}
      {lessons.length === 0 ? (
        <section className="rounded-2xl border border-dashed border-border bg-surface/20 p-10 text-center">
          <h2 className="text-xl font-semibold">No published lessons yet</h2>
          <p className="mt-2 text-sm text-secondary-text">Published lessons will be recommended here.</p>
        </section>
      ) : (
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {lessons.map((lesson) => {
            const isViewing = activeAction === `view:${lesson.id}`;
            const isDownloading = activeAction === `download:${lesson.id}`;
            return (
              <article key={lesson.id} className="flex min-h-64 flex-col rounded-2xl border border-border bg-secondary-bg p-5 shadow-lg shadow-stone-950/20">
                <header className="flex items-start gap-3">
                  <LessonFormatIcon format={lesson.format} />
                  <section className="min-w-0">
                    <h2 className="line-clamp-2 text-xl font-semibold leading-snug">{lesson.topic}</h2>
                    <p className="mt-1 text-sm text-secondary-text">
                      By{' '}
                      <Link
                        href={`/profile/${lesson.author_profile_id}`}
                        className="font-medium text-primary-text underline decoration-border underline-offset-4 transition-colors hover:text-accent"
                      >
                        {lesson.author_display_name}
                      </Link>
                    </p>
                  </section>
                </header>
                <p className="mt-4 line-clamp-4 text-sm leading-6 text-secondary-text">
                  {lesson.summary || 'A published Chalksmith lesson.'}
                </p>
                <section className="mt-auto flex gap-3 pt-6">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1 gap-1.5"
                    disabled={Boolean(activeAction)}
                    onClick={() => void viewLesson(lesson.id)}
                  >
                    <ExternalLink size={14} />
                    {isViewing ? 'Opening…' : 'View'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 gap-1.5"
                    disabled={Boolean(activeAction)}
                    onClick={() => void downloadLesson(lesson.id)}
                  >
                    <Download size={14} />
                    {isDownloading ? 'Preparing…' : 'Download'}
                  </Button>
                </section>
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
}
