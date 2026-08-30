'use client';

import { CirclePlus } from 'lucide-react';
import { useState } from 'react';

import DashboardShell from '@/components/dashboard/DashboardShell';
import CreateLessonSetModal from '@/components/lesson-sets/CreateLessonSetModal';
import LessonSetCard from '@/components/lesson-sets/LessonSetCard';
import { useLessonSets } from '@/lib/hooks/useLessonSets';

export default function LessonSetsPage() {
  const { lessonSets, isLoading, error, createLessonSet, deleteLessonSet } = useLessonSets();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <DashboardShell layoutId="lesson-sets-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg px-8 pb-8 pt-5">
        <header className="mb-5">
          <h1 className="text-3xl font-bold tracking-tight">Lesson Sets</h1>
          <p className="mt-2 text-sm text-secondary-text">Build reusable collections from lessons in your workspace.</p>
        </header>
        {error && <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">{error}</p>}
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-secondary-bg p-5 text-center shadow-lg shadow-stone-950/20 transition-colors hover:border-accent hover:bg-surface/30"
          >
            <CirclePlus className="text-accent" size={55} />
            <span className="mt-4 text-lg">Create Lesson Set</span>
          </button>
          {isLoading && (
            <p className="min-h-64 rounded-2xl border border-border bg-secondary-bg p-5 text-sm text-secondary-text">Loading lesson sets…</p>
          )}
          {!isLoading && lessonSets.length === 0 && (
            <section className="flex min-h-64 flex-col justify-center rounded-2xl border border-border bg-secondary-bg p-6">
              <h2 className="text-lg font-semibold text-primary-text">Plan a reusable lesson set</h2>
              <p className="mt-3 text-sm leading-6 text-secondary-text">
                Folders organize where lessons are stored. Lesson sets group lessons without moving or duplicating them.
              </p>
            </section>
          )}
          {!isLoading && lessonSets.map((lessonSet) => (
            <LessonSetCard
              key={lessonSet.id}
              lessonSet={lessonSet}
              onDelete={() => deleteLessonSet(lessonSet.id)}
            />
          ))}
        </section>
        <CreateLessonSetModal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          onCreate={async (title, description) => { await createLessonSet(title, description); }}
        />
      </section>
    </DashboardShell>
  );
}
