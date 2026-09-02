'use client';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import { useLessons } from '@/lib/hooks/useLessons';

export default function Dashboard() {
  const { folders, selectedFolderId, resolveFolderId } = useLessonFolders();
  const {
    lessons,
    isLoading,
    isLoadingMore,
    hasMore,
    error,
    loadMore,
    removeLesson,
    moveLessonToFolder,
  } = useLessons({ folderId: selectedFolderId });
  const normalizedLessons = lessons.map((lesson) => ({ ...lesson, folder_id: resolveFolderId(lesson.folder_id) }));
  const selectedFolder = folders.find((folder) => folder.id === selectedFolderId);

  return (
    <DashboardShell layoutId="dashboard-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg px-8 pb-8 pt-5">
        <header className="mb-5">
          <h2 className="text-3xl font-bold tracking-tight">{selectedFolder?.name ?? 'Lessons'}</h2>
        </header>
        {error && (
          <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
            {error}
          </p>
        )}
        {!isLoading && selectedFolderId && normalizedLessons.length === 0 && (
          <section className="mb-5 rounded-xl border border-dashed border-border bg-secondary-bg p-5">
            <h3 className="font-semibold text-primary-text">This folder is empty</h3>
            <p className="mt-1 text-sm text-secondary-text">
              Move an existing lesson here or create a new lesson. Folders organize where lessons are stored.
            </p>
          </section>
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
          showCreateCard
        />
      </section>
    </DashboardShell>
  );
}
