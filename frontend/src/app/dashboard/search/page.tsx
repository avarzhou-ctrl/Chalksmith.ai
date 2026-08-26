'use client';

import { useState } from 'react';
import { Search, X } from 'lucide-react';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import SearchFilter from '@/components/dashboard/SearchFilter';
import { useLessons } from '@/lib/hooks/useLessons';
import type { LessonFormat } from '@/lib/types/api';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [format, setFormat] = useState('');
  const { lessons, isLoading, error, removeLesson, moveLessonToFolder } = useLessons(
    {
      q: query.trim() || undefined,
      format: (format || undefined) as LessonFormat | undefined,
    },
    300,
  );
  const { folders, resolveFolderId } = useLessonFolders();
  const normalizedLessons = lessons.map((lesson) => ({ ...lesson, folder_id: resolveFolderId(lesson.folder_id) }));

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
        </header>

        {error && (
          <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
            {error}
          </p>
        )}

        <LessonGrid
          lessons={normalizedLessons}
          isLoading={isLoading}
          onDelete={(lessonId) => void removeLesson(lessonId)}
          onMove={moveLessonToFolder}
          folders={folders}
        />
      </section>
    </DashboardShell>
  );
}
