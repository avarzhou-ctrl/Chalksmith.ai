'use client';

import { useAuth } from '@clerk/nextjs';
import { ArrowLeft, Download } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import PublishedLessonLikeButton from '@/components/content/PublishedLessonLikeButton';
import LessonViewport from '@/components/generation/LessonViewport';
import Skeleton, { ChalkLoader } from '@/components/ui/Skeleton';
import { createPublicApiClient } from '@/lib/api/client';
import {
  getPublishedLesson,
  getPublishedLessonAccessUrl,
  listLikedPublishedLessonIds,
  setPublishedLessonLike,
} from '@/lib/api/explore';
import { useApi } from '@/lib/hooks/useApi';
import type { PublishedLessonItem } from '@/lib/types/api';

export default function PublishedLessonClient() {
  const params = useParams<{ lessonId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const lessonId = params.lessonId;
  const requestedReturnTo = searchParams.get('returnTo');
  const isAllowedReturnTo = requestedReturnTo === '/dashboard/published'
    || requestedReturnTo?.startsWith('/dashboard/published?')
    || requestedReturnTo === '/content'
    || requestedReturnTo?.startsWith('/content?');
  const returnTo = requestedReturnTo && isAllowedReturnTo
    ? requestedReturnTo
    : '/content';
  const publicApi = useMemo(() => createPublicApiClient(), []);
  const authenticatedApi = useApi();
  const { isLoaded: authLoaded, isSignedIn } = useAuth();
  const [lesson, setLesson] = useState<PublishedLessonItem | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isPreviewReady, setIsPreviewReady] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isUpdatingLike, setIsUpdatingLike] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setIsPreviewReady(false);
    setError(null);
    Promise.all([
      getPublishedLesson(publicApi, lessonId, controller.signal),
      getPublishedLessonAccessUrl(publicApi, lessonId, false, controller.signal),
    ])
      .then(([lessonData, access]) => {
        setLesson(lessonData);
        setPreviewUrl(access.url);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load this lesson.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [lessonId, publicApi]);

  useEffect(() => {
    if (!authLoaded || !isSignedIn || !lesson) {
      setIsLiked(false);
      return;
    }
    const controller = new AbortController();
    listLikedPublishedLessonIds(authenticatedApi, [lesson.root_lesson_id], controller.signal)
      .then((rootIds) => setIsLiked(rootIds.includes(lesson.root_lesson_id)))
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load your like.');
        }
      });
    return () => controller.abort();
  }, [authLoaded, authenticatedApi, isSignedIn, lesson]);

  async function downloadLesson() {
    setIsDownloading(true);
    setError(null);
    try {
      const access = await getPublishedLessonAccessUrl(publicApi, lessonId, true);
      window.location.assign(access.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to download this lesson.');
    } finally {
      setIsDownloading(false);
    }
  }

  async function toggleLike() {
    if (!lesson) return;
    setIsUpdatingLike(true);
    setError(null);
    try {
      const result = await setPublishedLessonLike(authenticatedApi, lesson.id, !isLiked);
      setIsLiked(result.liked);
      setLesson((current) => current ? { ...current, like_count: result.like_count } : current);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to update this like.');
    } finally {
      setIsUpdatingLike(false);
    }
  }

  return (
    <main className="app-route-without-site-header flex h-screen flex-col overflow-hidden bg-primary-bg font-sans text-primary-text">
      <header className="flex shrink-0 items-center gap-4 border-b border-border bg-secondary-bg px-5 py-3">
        <button
          type="button"
          onClick={() => router.push(returnTo)}
          className="grid size-9 shrink-0 place-items-center rounded-lg text-secondary-text transition-colors hover:bg-primary-text/10 hover:text-primary-text"
          aria-label="Back to published lessons"
        >
          <ArrowLeft size={18} />
        </button>
        <Link href="/dashboard" className="grid size-9 shrink-0 place-items-center rounded-lg" aria-label="Dashboard">
          <img src="/logo.png" alt="" className="size-7 object-contain" />
        </Link>
        <section className="min-w-0 flex-1">
          {isLoading ? (
            <Skeleton className="h-6 w-48" />
          ) : (
            <h1 className="truncate text-lg font-semibold">{lesson?.topic || 'Published lesson'}</h1>
          )}
          {lesson && (
            <p className="truncate text-xs text-secondary-text">
              By{' '}
              <Link href={`/profile/${lesson.author_profile_id}`} className="hover:text-accent">
                {lesson.author_display_name}
              </Link>
            </p>
          )}
        </section>
        {lesson && (
          <section className="flex shrink-0 items-center gap-2">
            <PublishedLessonLikeButton
              count={lesson.like_count}
              isLiked={isLiked}
              isSignedIn={Boolean(isSignedIn)}
              isBusy={isUpdatingLike}
              onToggle={() => void toggleLike()}
            />
            <button
              type="button"
              disabled={isDownloading}
              onClick={() => void downloadLesson()}
              className="inline-flex min-h-8 items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-xs font-medium text-secondary-text transition-colors hover:border-accent hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent disabled:cursor-wait disabled:opacity-60"
            >
              <Download size={14} aria-hidden="true" />
              {isDownloading ? 'Preparing…' : 'Download'}
            </button>
          </section>
        )}
        {isLoading && <Skeleton className="h-9 w-32 rounded-lg" />}
      </header>

      {error && (
        <p className="mx-5 mt-4 shrink-0 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
          {error}
        </p>
      )}

      <section className="relative flex min-h-0 flex-1 items-center justify-center p-5">
        <article className="relative flex size-full max-w-7xl flex-col overflow-hidden rounded-3xl border border-border bg-stone-950 shadow-2xl">
          {isLoading ? (
            <section className="grid size-full place-items-center" aria-busy="true">
              <ChalkLoader label="Loading published lesson" />
            </section>
          ) : lesson && previewUrl ? (
            <>
              <LessonViewport>
                {lesson.format === 'video' ? (
                  <video
                    className={`size-full bg-black object-contain transition-opacity duration-200 ${isPreviewReady ? 'opacity-100' : 'opacity-0'}`}
                    src={previewUrl}
                    controls
                    autoPlay
                    onLoadedData={() => setIsPreviewReady(true)}
                  />
                ) : (
                  <iframe
                    src={previewUrl}
                    className={`size-full border-none bg-primary-bg transition-opacity duration-200 ${isPreviewReady ? 'opacity-100' : 'opacity-0'}`}
                    title={lesson.topic}
                    sandbox="allow-scripts"
                    onLoad={() => setIsPreviewReady(true)}
                  />
                )}
              </LessonViewport>
              {!isPreviewReady && (
                <section className="absolute inset-0 grid place-items-center bg-stone-950" aria-busy="true">
                  <ChalkLoader label="Loading published lesson" />
                </section>
              )}
            </>
          ) : (
            <section className="m-auto max-w-md p-8 text-center">
              <h2 className="text-xl font-semibold">Lesson unavailable</h2>
              <p className="mt-2 text-sm text-secondary-text">
                This lesson may no longer be published.
              </p>
            </section>
          )}
        </article>
      </section>
    </main>
  );
}
