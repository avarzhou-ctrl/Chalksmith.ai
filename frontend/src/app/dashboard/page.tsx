'use client';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import { useLessons } from '@/lib/hooks/useLessons';

export default function Dashboard() {
  const { lessons, isLoading, error, removeLesson, moveLessonToFolder } = useLessons();
  const { folders, selectedFolderId, resolveFolderId } = useLessonFolders();
  const normalizedLessons = lessons.map((lesson) => ({ ...lesson, folder_id: resolveFolderId(lesson.folder_id) }));
  const visibleLessons = normalizedLessons.filter((lesson) => lesson.folder_id === selectedFolderId);
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
        <LessonGrid
          lessons={visibleLessons}
          isLoading={isLoading}
          onDelete={(lessonId) => void removeLesson(lessonId)}
          onMove={moveLessonToFolder}
          folders={folders}
          showCreateCard
        />
      </section>
    </DashboardShell>
  );
}
