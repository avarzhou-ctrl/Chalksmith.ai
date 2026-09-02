'use client';

import { useEffect, useState } from 'react';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import LessonSearchControls from '@/components/lesson/LessonSearchControls';
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

  return (
    <DashboardShell layoutId="search-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg p-8">
        <header className="mb-6">
          <h2 className="mb-5 text-3xl font-bold tracking-tight text-primary-text">Search</h2>
          <LessonSearchControls
            query={query}
            format={format}
            tags={availableTags}
            selectedTags={selectedTags}
            queryPlaceholder="Search lessons"
            queryAriaLabel="Search lessons"
            tagsAriaLabel="Filter lessons by tag"
            onQueryChange={setQuery}
            onFormatChange={setFormat}
            onSelectedTagsChange={setSelectedTags}
          />
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
