'use client';

import PublishedLessonGrid from '@/components/content/PublishedLessonGrid';
import DashboardShell from '@/components/dashboard/DashboardShell';

export default function PublishedLessonsPage() {
  return (
    <DashboardShell layoutId="published-lessons-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg px-8 pb-8 pt-5">
        <header className="mb-5">
          <h1 className="text-3xl font-bold tracking-tight">Published Lessons</h1>
          <p className="mt-2 text-sm text-secondary-text">
            View the lessons you have shared with the Chalksmith community.
          </p>
        </header>
        <PublishedLessonGrid
          query=""
          format={undefined}
          tags={[]}
          ownerOnly
          returnTo="/dashboard/published"
        />
      </section>
    </DashboardShell>
  );
}
