'use client';

import { BookOpen, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import ActionMenu from '@/components/ui/ActionMenu';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import LessonFormatIcon from '@/components/lesson/LessonFormatIcon';
import type { LessonSetListItem } from '@/lib/types/api';

interface LessonSetCardProps {
  lessonSet: LessonSetListItem;
  onDelete: () => Promise<void>;
}

export default function LessonSetCard({ lessonSet, onDelete }: LessonSetCardProps) {
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const formattedDate = new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(lessonSet.updated_at));

  async function confirmDelete() {
    try {
      setIsDeleting(true);
      setError(null);
      await onDelete();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to delete lesson set.');
      setIsDeleting(false);
    }
  }

  return (
    <article className="relative flex min-h-64 flex-col rounded-2xl border border-border bg-secondary-bg p-5 shadow-lg shadow-stone-950/20">
      <Link href={`/dashboard/sets/${lessonSet.id}`} className="absolute inset-0 rounded-2xl" title={`Open ${lessonSet.title}`} />
      <header className="pointer-events-none relative z-10 flex items-start gap-3">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent">
          <BookOpen size={22} />
        </span>
        <section className="min-w-0 flex-1">
          <h2 className="line-clamp-2 text-xl font-semibold leading-snug text-primary-text">{lessonSet.title}</h2>
          <p className="mt-1 text-sm text-secondary-text">Updated {formattedDate}</p>
        </section>
        <section className="pointer-events-auto">
          <ActionMenu
            label={`Actions for ${lessonSet.title}`}
            items={[{ label: 'Delete', icon: Trash2, onSelect: () => setIsDeleteOpen(true) }]}
          />
        </section>
      </header>
      <p className="pointer-events-none relative z-10 mt-4 line-clamp-2 text-sm leading-6 text-secondary-text">
        {lessonSet.description || 'A reusable collection of Chalksmith lessons.'}
      </p>
      <section className="pointer-events-none relative z-10 mt-4">
        {lessonSet.preview_lessons.length > 0 ? (
          <ol className="space-y-2">
            {lessonSet.preview_lessons.map((lesson, index) => (
              <li key={lesson.root_lesson_id} className="flex items-center gap-2 rounded-lg bg-primary-bg/70 px-2.5 py-2">
                <span className="grid size-5 shrink-0 place-items-center rounded-full bg-surface text-xs font-semibold text-secondary-text">
                  {index + 1}
                </span>
                <LessonFormatIcon format={lesson.format} />
                <span className="min-w-0 flex-1 truncate text-xs font-medium text-primary-text">{lesson.topic}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="rounded-lg border border-dashed border-border bg-primary-bg/50 px-3 py-3 text-xs text-secondary-text">
            Empty sequence — add lessons to begin planning.
          </p>
        )}
        {lessonSet.lesson_count > lessonSet.preview_lessons.length && (
          <p className="mt-2 text-xs text-secondary-text">+{lessonSet.lesson_count - lessonSet.preview_lessons.length} more in sequence</p>
        )}
      </section>
      <footer className="pointer-events-none relative z-10 mt-auto pt-6 text-xs text-secondary-text">
        {lessonSet.lesson_count} {lessonSet.lesson_count === 1 ? 'lesson' : 'lessons'}
      </footer>

      <Modal isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} title="Delete lesson set?">
        <p>Lessons in this set will not be deleted.</p>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        <span className="mt-6 flex gap-3">
          <Button type="button" variant="secondary" className="w-full" onClick={() => setIsDeleteOpen(false)}>Cancel</Button>
          <Button type="button" className="w-full" disabled={isDeleting} onClick={() => void confirmDelete()}>
            {isDeleting ? 'Deleting…' : 'Delete'}
          </Button>
        </span>
      </Modal>
    </article>
  );
}
