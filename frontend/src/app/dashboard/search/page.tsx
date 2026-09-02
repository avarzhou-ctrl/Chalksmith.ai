'use client';

import { useEffect, useState } from 'react';
import { Search, X } from 'lucide-react';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import SearchFilter from '@/components/dashboard/SearchFilter';
import TagFilterChips from '@/components/ui/TagFilterChips';
import { listLessonTags } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import { useLessons } from '@/lib/hooks/useLessons';
import type { LessonFormat, LessonTagItem } from '@/lib/types/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [format, setFormat] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<LessonTagItem[]>([]);
  const [tagError, setTagError] = useState<string | null>(null);
  const api = useApi();
  const {
    lessons,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    loadMore,
    removeLesson,
    moveLessonToFolder,
  } = useLessons(
    {
      q: query.trim() || undefined,
      format: (format || undefined) as LessonFormat | undefined,
      tags: selectedTags,
    },
    300,
  );
  const { folders, resolveFolderId } = useLessonFolders();
  const normalizedLessons = lessons.map((lesson) => ({ ...lesson, folder_id: resolveFolderId(lesson.folder_id) }));

  useEffect(() => {
    const controller = new AbortController();
    listLessonTags(api, controller.signal)
      .then(setAvailableTags)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setTagError(caught instanceof Error ? caught.message : 'Failed to load tags.');
        }
      });
    return () => controller.abort();
  }, [api]);

  function toggleTag(value: string) {
    setSelectedTags((current) => (
      current.includes(value)
        ? current.filter((tag) => tag !== value)
        : [...current, value]
    ));
  }

  return (
    <DashboardShell layoutId="search-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg p-8">
        <header className="mb-6">
          <h2 className="mb-5 text-3xl font-bold tracking-tight text-primary-text">Search</h2>
          <div className="flex flex-col gap-3 lg:flex-row">
            <label className="relative flex min-h-12 flex-1 items-center rounded-lg border border-border bg-secondary-bg text-primary-text focus-within:border-accent">
              <Search className="ml-4 shrink-0 text-secondary-text" size={20} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search lessons"
                className="h-12 min-w-0 flex-1 bg-transparent px-3 text-sm text-primary-text outline-none placeholder:text-secondary-text"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className="mr-3 rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10 hover:text-primary-text focus:outline-none focus:ring-2"
                  title="Clear search"
                >
                  <X size={18} />
                </button>
              )}
            </label>

            <div className="w-full lg:w-64">
              <SearchFilter format={format} onFormatChange={setFormat} />
            </div>
          </div>
          <section className="mt-4 flex flex-col gap-3">
            <TagFilterChips
              tags={availableTags}
              selected={selectedTags}
              onToggle={toggleTag}
              ariaLabel="Filter lessons by tag"
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
          </section>
        </header>

        {(error || tagError) && (
          <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
            {error || tagError}
          </p>
        )}

        <LessonGrid
          lessons={normalizedLessons}
          isLoading={isLoading}
          isLoadingMore={isLoadingMore}
          hasMore={hasMore}
          onLoadMore={loadMore}
          onDelete={(lessonId) => void removeLesson(lessonId)}
          onMove={moveLessonToFolder}
          folders={folders}
        />
      </section>
    </DashboardShell>
  );
}
