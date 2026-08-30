'use client';

import { BookPlus, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';

import CreateLessonSetModal from '@/components/lesson-sets/CreateLessonSetModal';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';
import { addLessonToSet, createLessonSet, listLessonSets } from '@/lib/api/lesson-sets';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonSetListItem } from '@/lib/types/api';

interface AddToLessonSetModalProps {
  isOpen: boolean;
  lessonId: string;
  onClose: () => void;
  onAdded?: (lessonSetId: string) => void;
}

export default function AddToLessonSetModal({ isOpen, lessonId, onClose, onAdded }: AddToLessonSetModalProps) {
  const api = useApi();
  const [lessonSets, setLessonSets] = useState<LessonSetListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [busySetId, setBusySetId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const controller = new AbortController();
    setIsLoading(true);
    setMessage(null);
    setError(null);
    listLessonSets(api, controller.signal)
      .then(setLessonSets)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load lesson sets.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, isOpen]);

  async function addToSet(lessonSet: LessonSetListItem) {
    try {
      setBusySetId(lessonSet.id);
      setMessage(null);
      setError(null);
      const updated = await addLessonToSet(api, lessonSet.id, lessonId);
      setLessonSets((current) => current.map((candidate) => (
        candidate.id === updated.id
          ? {
              ...candidate,
              lesson_count: updated.lessons.length,
              preview_lessons: updated.lessons.slice(0, 3),
              updated_at: updated.updated_at,
            }
          : candidate
      )));
      onAdded?.(lessonSet.id);
      setMessage(`Added to ${lessonSet.title}.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to add lesson to set.');
    } finally {
      setBusySetId(null);
    }
  }

  async function createAndAdd(title: string, description: string) {
    const created = await createLessonSet(api, title, description);
    const updated = await addLessonToSet(api, created.id, lessonId);
    setLessonSets((current) => [{
      id: updated.id,
      title: updated.title,
      description: updated.description,
      lesson_count: updated.lessons.length,
      preview_lessons: updated.lessons.slice(0, 3),
      created_at: updated.created_at,
      updated_at: updated.updated_at,
    }, ...current]);
    onAdded?.(updated.id);
    setMessage(`Created ${updated.title} and added the lesson.`);
  }

  return (
    <>
      <Modal isOpen={isOpen && !isCreateOpen} onClose={onClose} title="Add to lesson set">
        <section className="text-left">
          <Button type="button" variant="outline" className="mb-4 w-full gap-2" onClick={() => setIsCreateOpen(true)}>
            <Plus size={16} />
            Create new set
          </Button>
          {isLoading && lessonSets.length === 0 && (
            <section className="space-y-2 py-1" aria-busy="true">
              {Array.from({ length: 3 }, (_, index) => <Skeleton key={index} className="h-14 w-full rounded-lg" />)}
              <SkeletonStatus>Loading lesson sets</SkeletonStatus>
            </section>
          )}
          {isLoading && lessonSets.length > 0 && <SkeletonStatus>Refreshing lesson sets</SkeletonStatus>}
          {!isLoading && lessonSets.length === 0 && (
            <p className="py-4 text-center text-sm">Create your first lesson set to group related lessons.</p>
          )}
          <ul className="space-y-2" aria-busy={isLoading}>
            {lessonSets.map((lessonSet) => (
              <li key={lessonSet.id}>
                <button
                  type="button"
                  disabled={busySetId !== null}
                  onClick={() => void addToSet(lessonSet)}
                  className="flex min-h-12 w-full items-center gap-3 rounded-lg border border-border bg-primary-bg px-3 py-2 text-left transition-colors hover:border-accent disabled:opacity-50"
                >
                  <BookPlus size={18} className="shrink-0 text-accent" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-primary-text">{lessonSet.title}</span>
                    <span className="text-xs text-secondary-text">{lessonSet.lesson_count} lessons</span>
                  </span>
                  {busySetId === lessonSet.id && <span className="text-xs text-secondary-text">Adding…</span>}
                </button>
              </li>
            ))}
          </ul>
          {message && <p className="mt-4 rounded-lg bg-emerald-950/40 p-3 text-sm text-emerald-300">{message}</p>}
          {error && <p className="mt-4 rounded-lg bg-red-950/40 p-3 text-sm text-red-300">{error}</p>}
        </section>
      </Modal>
      <CreateLessonSetModal
        isOpen={isOpen && isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreate={createAndAdd}
      />
    </>
  );
}
