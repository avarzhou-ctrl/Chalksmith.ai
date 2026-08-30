'use client';

import { ArrowLeft, Plus, Save } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

import DashboardShell from '@/components/dashboard/DashboardShell';
import AddLessonsToSetModal from '@/components/lesson-sets/AddLessonsToSetModal';
import LessonSetLessonRow from '@/components/lesson-sets/LessonSetLessonRow';
import Button from '@/components/ui/Button';
import {
  getLessonSet,
  removeLessonFromSet,
  reorderLessonSet,
  updateLessonSet,
} from '@/lib/api/lesson-sets';
import { useApi } from '@/lib/hooks/useApi';
import { dispatchLessonSetsChanged } from '@/lib/lesson-drag';
import type { LessonSetDetail } from '@/lib/types/api';

export default function LessonSetDetailPage() {
  const { setId } = useParams<{ setId: string }>();
  const api = useApi();
  const [lessonSet, setLessonSet] = useState<LessonSetDetail | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    getLessonSet(api, setId, controller.signal)
      .then((data) => {
        setLessonSet(data);
        setTitle(data.title);
        setDescription(data.description);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load lesson set.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, setId]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!lessonSet || !title.trim()) return;
    try {
      setIsSaving(true);
      setError(null);
      const updated = await updateLessonSet(api, lessonSet.id, {
        title: title.trim(),
        description: description.trim(),
      });
      setLessonSet(updated);
      setTitle(updated.title);
      setDescription(updated.description);
      dispatchLessonSetsChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to save lesson set.');
    } finally {
      setIsSaving(false);
    }
  }

  async function moveLesson(index: number, direction: -1 | 1) {
    if (!lessonSet) return;
    const target = index + direction;
    if (target < 0 || target >= lessonSet.lessons.length) return;
    const reordered = [...lessonSet.lessons];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    try {
      setIsMutating(true);
      setError(null);
      const updated = await reorderLessonSet(
        api,
        lessonSet.id,
        reordered.map((lesson) => lesson.root_lesson_id),
      );
      setLessonSet(updated);
      dispatchLessonSetsChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to reorder lessons.');
    } finally {
      setIsMutating(false);
    }
  }

  async function removeLesson(rootLessonId: string) {
    if (!lessonSet) return;
    try {
      setIsMutating(true);
      setError(null);
      setLessonSet(await removeLessonFromSet(api, lessonSet.id, rootLessonId));
      dispatchLessonSetsChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to remove lesson.');
    } finally {
      setIsMutating(false);
    }
  }

  return (
    <DashboardShell layoutId="lesson-set-detail-layout">
      <section className="flex h-full flex-col overflow-y-auto bg-primary-bg px-8 pb-8 pt-5">
        <header className="mb-6 flex items-center justify-between gap-4">
          <Link href="/dashboard/sets" className="inline-flex items-center gap-2 text-sm text-secondary-text hover:text-accent">
            <ArrowLeft size={18} />
            Lesson Sets
          </Link>
          {lessonSet && (
            <Button type="button" className="gap-2" onClick={() => setIsAddOpen(true)}>
              <Plus size={17} />
              Add lessons
            </Button>
          )}
        </header>

        {error && <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/30 p-3 text-sm text-red-200">{error}</p>}
        {isLoading && <p className="text-sm text-secondary-text">Loading lesson set…</p>}
        {!isLoading && !lessonSet && !error && <p className="text-sm text-secondary-text">Lesson set not found.</p>}

        {lessonSet && (
          <>
            <form onSubmit={save} className="mb-8 rounded-2xl border border-border bg-secondary-bg p-5">
              <label htmlFor="set-title" className="text-sm font-medium text-primary-text">Set title</label>
              <input
                id="set-title"
                maxLength={160}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                className="mt-2 h-12 w-full rounded-lg border border-border bg-primary-bg px-4 text-xl font-semibold text-primary-text outline-none focus:border-accent"
              />
              <label htmlFor="set-description" className="mt-5 block text-sm font-medium text-primary-text">Description</label>
              <textarea
                id="set-description"
                maxLength={2000}
                rows={3}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                className="mt-2 w-full resize-none rounded-lg border border-border bg-primary-bg p-4 text-primary-text outline-none focus:border-accent"
              />
              <span className="mt-4 flex justify-end">
                <Button type="submit" disabled={isSaving || !title.trim()} className="gap-2">
                  <Save size={16} />
                  {isSaving ? 'Saving…' : 'Save details'}
                </Button>
              </span>
            </form>

            <section>
              <header className="mb-4 flex items-end justify-between">
                <section>
                  <h2 className="text-xl font-semibold">Lessons</h2>
                  <p className="mt-1 text-sm text-secondary-text">The order below becomes the teaching sequence.</p>
                </section>
                <span className="text-sm text-secondary-text">{lessonSet.lessons.length} / 50</span>
              </header>
              {lessonSet.lessons.length === 0 ? (
                <button
                  type="button"
                  onClick={() => setIsAddOpen(true)}
                  className="w-full rounded-2xl border border-dashed border-border bg-secondary-bg p-10 text-center text-secondary-text hover:border-accent hover:text-accent"
                >
                  Add the first lesson to this set
                </button>
              ) : (
                <ol className="space-y-3">
                  {lessonSet.lessons.map((lesson, index) => (
                    <LessonSetLessonRow
                      key={lesson.root_lesson_id}
                      lesson={lesson}
                      index={index}
                      total={lessonSet.lessons.length}
                      isBusy={isMutating}
                      onMove={(direction) => void moveLesson(index, direction)}
                      onRemove={() => void removeLesson(lesson.root_lesson_id)}
                    />
                  ))}
                </ol>
              )}
            </section>
            <AddLessonsToSetModal
              isOpen={isAddOpen}
              lessonSet={lessonSet}
              onClose={() => setIsAddOpen(false)}
              onChange={(updated) => {
                setLessonSet(updated);
                dispatchLessonSetsChanged();
              }}
            />
          </>
        )}
      </section>
    </DashboardShell>
  );
}
