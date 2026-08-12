'use client';

import DashboardShell from '@/components/dashboard/DashboardShell';
import LessonGrid from '@/components/dashboard/LessonGrid';
import { useLessons } from '@/lib/hooks/useLessons';

export default function Dashboard() {
  const { lessons, isLoading, error, removeLesson } = useLessons();

  return (
    <DashboardShell layoutId="dashboard-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg p-8">
        <header className="mb-2">
          <h2 className="text-3xl font-bold tracking-tight">Lessons</h2>
        </header>
        {error && (
          <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">
            {error}
          </p>
        )}
        <LessonGrid
          lessons={lessons}
          isLoading={isLoading}
          onDelete={(lessonId) => void removeLesson(lessonId)}
          showCreateCard
        />
      </section>
    </DashboardShell>
  );
}
