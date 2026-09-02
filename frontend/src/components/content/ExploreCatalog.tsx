'use client';

import { useEffect, useMemo, useState } from 'react';

import PublishedLessonGrid from '@/components/content/PublishedLessonGrid';
import LessonCardSkeleton from '@/components/lesson/LessonCardSkeleton';
import LessonSearchControls from '@/components/lesson/LessonSearchControls';
import { SkeletonStatus } from '@/components/ui/Skeleton';
import { createPublicApiClient } from '@/lib/api/client';
import { listPublishedTags } from '@/lib/api/explore';
import type { LessonFormat, PublishedTagItem } from '@/lib/types/api';

export default function ExploreCatalog() {
  const api = useMemo(() => createPublicApiClient(), []);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [format, setFormat] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<PublishedTagItem[]>([]);
  const [tagError, setTagError] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initialQuery = params.get('q') || '';
    setQuery(initialQuery);
    setDebouncedQuery(initialQuery);
    setFormat(params.get('format') || '');
    setSelectedTags(params.getAll('tag'));
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setDebouncedQuery(query), 300);
    return () => window.clearTimeout(timeoutId);
  }, [query]);

  useEffect(() => {
    const controller = new AbortController();
    listPublishedTags(api, controller.signal)
      .then(setAvailableTags)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setTagError(caught instanceof Error ? caught.message : 'Failed to load tags.');
        }
      });
    return () => controller.abort();
  }, [api]);

  useEffect(() => {
    if (!isHydrated) return;
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    if (format) params.set('format', format);
    selectedTags.forEach((tag) => params.append('tag', tag));
    const suffix = params.size ? `?${params}` : '';
    window.history.replaceState({}, '', `${window.location.pathname}${suffix}`);
  }, [format, isHydrated, query, selectedTags]);

  return (
    <>
      <section className="my-8">
        <LessonSearchControls
          query={query}
          format={format}
          tags={availableTags}
          selectedTags={selectedTags}
          queryPlaceholder="Search lessons, tags, or creators"
          queryAriaLabel="Search published lessons"
          tagsAriaLabel="Filter published lessons by tag"
          onQueryChange={setQuery}
          onFormatChange={setFormat}
          onSelectedTagsChange={setSelectedTags}
        />
        {tagError && <p className="mt-3 text-sm text-red-300">{tagError}</p>}
      </section>

      {isHydrated && (
        <PublishedLessonGrid
          query={debouncedQuery}
          format={(format || undefined) as LessonFormat | undefined}
          tags={selectedTags}
          returnTo={`${window.location.pathname}${window.location.search}`}
        />
      )}
      {!isHydrated && (
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3" aria-busy="true">
          {Array.from({ length: 3 }, (_, index) => <LessonCardSkeleton key={index} />)}
          <SkeletonStatus>Loading published lessons</SkeletonStatus>
        </section>
      )}
    </>
  );
}
