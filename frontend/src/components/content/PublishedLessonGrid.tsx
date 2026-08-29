'use client';

import { useAuth } from '@clerk/nextjs';
import { Download, Eye } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

import PublishedLessonLikeButton from '@/components/content/PublishedLessonLikeButton';
import LessonCardLayout from '@/components/lesson/LessonCardLayout';
import { createPublicApiClient } from '@/lib/api/client';
import {
  getPublishedLessonAccessUrl,
  listLikedPublishedLessonIds,
  listMyPublishedLessons,
  listPublishedLessons,
  setPublishedLessonLike,
} from '@/lib/api/explore';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonFormat, PublishedLessonItem } from '@/lib/types/api';

interface PublishedLessonGridProps {
  query: string;
  format: LessonFormat | undefined;
  tags: string[];
  ownerOnly?: boolean;
  returnTo?: string;
}

export default function PublishedLessonGrid({
  query,
  format,
  tags,
  ownerOnly = false,
  returnTo = '/content',
}: PublishedLessonGridProps) {
  const publicApi = useMemo(() => createPublicApiClient(), []);
  const authenticatedApi = useApi();
  const { isLoaded: authLoaded, isSignedIn } = useAuth();
  const [lessons, setLessons] = useState<PublishedLessonItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingLessonId, setDownloadingLessonId] = useState<string | null>(null);
  const [likingRootId, setLikingRootId] = useState<string | null>(null);
  const [likedRootIds, setLikedRootIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const tagKey = tags.join('\u0000');

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    const request = ownerOnly
      ? listMyPublishedLessons(authenticatedApi, controller.signal)
      : listPublishedLessons(
          publicApi,
          { q: query.trim() || undefined, format, tags },
          controller.signal,
        );
    request
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
  }, [authenticatedApi, publicApi, format, ownerOnly, query, tagKey]);

  useEffect(() => {
    if (!authLoaded || !isSignedIn || lessons.length === 0) {
      setLikedRootIds(new Set());
      return;
    }
    const controller = new AbortController();
    listLikedPublishedLessonIds(
      authenticatedApi,
      lessons.map((lesson) => lesson.root_lesson_id),
      controller.signal,
    )
      .then((rootIds) => setLikedRootIds(new Set(rootIds)))
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load your likes.');
        }
      });
    return () => controller.abort();
  }, [authLoaded, authenticatedApi, isSignedIn, lessons]);

  async function downloadLesson(lessonId: string) {
    setDownloadingLessonId(lessonId);
    setError(null);
    try {
      const access = await getPublishedLessonAccessUrl(publicApi, lessonId, true);
      window.location.assign(access.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to download this lesson.');
    } finally {
      setDownloadingLessonId(null);
    }
  }

  async function toggleLike(lesson: PublishedLessonItem) {
    const nextLiked = !likedRootIds.has(lesson.root_lesson_id);
    setLikingRootId(lesson.root_lesson_id);
    setError(null);
    try {
      const result = await setPublishedLessonLike(authenticatedApi, lesson.id, nextLiked);
      setLikedRootIds((current) => {
        const next = new Set(current);
        if (result.liked) next.add(result.root_lesson_id);
        else next.delete(result.root_lesson_id);
        return next;
      });
      setLessons((current) => current.map((candidate) => (
        candidate.root_lesson_id === result.root_lesson_id
          ? { ...candidate, like_count: result.like_count }
          : candidate
      )));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to update this like.');
    } finally {
      setLikingRootId(null);
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
          <p className="mt-2 text-sm text-secondary-text">
            {query || format || tags.length
              ? 'Try a different search term or filter.'
              : 'Published lessons will be recommended here.'}
          </p>
        </section>
      ) : (
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {lessons.map((lesson) => {
            const isDownloading = downloadingLessonId === lesson.id;
            const isLiked = likedRootIds.has(lesson.root_lesson_id);
            return (
              <LessonCardLayout
                key={lesson.id}
                format={lesson.format}
                title={lesson.topic}
                subtitle={(
                  <p>
                    By{' '}
                    <Link
                      href={`/profile/${lesson.author_profile_id}`}
                      className="font-medium text-primary-text underline decoration-border underline-offset-4 transition-colors hover:text-accent"
                    >
                      {lesson.author_display_name}
                    </Link>
                  </p>
                )}
                subtitleInteractive
                description={lesson.summary || 'A published Chalksmith lesson.'}
                tags={lesson.tags}
                footer={(
                  <section className="flex min-h-8 items-center justify-between gap-3">
                    <section className="flex items-center gap-2">
                      <Link
                        href={`/content/${lesson.id}?returnTo=${encodeURIComponent(returnTo)}`}
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-lg bg-accent px-2.5 py-1.5 text-xs font-medium text-primary-text transition-colors hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <Eye size={14} aria-hidden="true" />
                        View
                      </Link>
                      <button
                        type="button"
                        disabled={isDownloading}
                        onClick={() => void downloadLesson(lesson.id)}
                        className="inline-flex min-h-8 items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium text-secondary-text transition-colors hover:border-accent hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent disabled:cursor-wait disabled:opacity-60"
                      >
                        <Download size={14} aria-hidden="true" />
                        {isDownloading ? 'Preparing…' : 'Download'}
                      </button>
                    </section>
                    <PublishedLessonLikeButton
                      count={lesson.like_count}
                      isLiked={isLiked}
                      isSignedIn={Boolean(isSignedIn)}
                      isBusy={likingRootId === lesson.root_lesson_id}
                      onToggle={() => void toggleLike(lesson)}
                    />
                  </section>
                )}
                footerInteractive
              />
            );
          })}
        </section>
      )}
    </section>
  );
}
