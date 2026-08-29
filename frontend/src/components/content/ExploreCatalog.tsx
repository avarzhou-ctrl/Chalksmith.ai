'use client';

import { Search, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import PublishedLessonGrid from '@/components/content/PublishedLessonGrid';
import SearchFilter from '@/components/dashboard/SearchFilter';
import TagFilterChips from '@/components/ui/TagFilterChips';
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

  function toggleTag(value: string) {
    setSelectedTags((current) => (
      current.includes(value)
        ? current.filter((tag) => tag !== value)
        : [...current, value]
    ));
  }

  return (
    <>
      <section className="my-8 flex flex-col gap-3">
        <section className="flex flex-col gap-3 lg:flex-row">
          <label className="flex min-h-12 flex-1 items-center rounded-xl border border-border bg-secondary-bg px-4 focus-within:border-accent">
            <Search size={20} className="shrink-0 text-secondary-text" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search published lessons"
              placeholder="Search lessons, tags, or creators"
              className="min-w-0 flex-1 bg-transparent px-3 text-sm text-primary-text outline-none placeholder:text-secondary-text"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="rounded-md p-1 text-secondary-text hover:bg-primary-text/10 hover:text-primary-text focus:outline-none focus:ring-2"
                aria-label="Clear search"
              >
                <X size={18} />
              </button>
            )}
          </label>
          <section className="w-full lg:w-64">
            <SearchFilter format={format} onFormatChange={setFormat} />
          </section>
        </section>
        <TagFilterChips
          tags={availableTags}
          selected={selectedTags}
          onToggle={toggleTag}
          ariaLabel="Filter published lessons by tag"
        />
        {(query || format || selectedTags.length > 0) && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setFormat('');
              setSelectedTags([]);
            }}
            className="w-fit text-xs font-medium text-accent hover:text-amber-500"
          >
            Clear all filters
          </button>
        )}
        {tagError && <p className="text-sm text-red-300">{tagError}</p>}
      </section>

      {isHydrated && (
        <PublishedLessonGrid
          query={debouncedQuery}
          format={(format || undefined) as LessonFormat | undefined}
          tags={selectedTags}
          returnTo={`${window.location.pathname}${window.location.search}`}
        />
      )}
    </>
  );
}
