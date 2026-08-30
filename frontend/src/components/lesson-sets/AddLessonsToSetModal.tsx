'use client';

import { Plus } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import LessonFormatIcon from '@/components/dashboard/LessonFormatIcon';
import Modal from '@/components/ui/Modal';
import { addLessonToSet } from '@/lib/api/lesson-sets';
import { listLessons } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonListItem, LessonSetDetail } from '@/lib/types/api';

interface AddLessonsToSetModalProps {
  isOpen: boolean;
  lessonSet: LessonSetDetail;
  onClose: () => void;
  onChange: (lessonSet: LessonSetDetail) => void;
}

export default function AddLessonsToSetModal({
  isOpen,
  lessonSet,
  onClose,
  onChange,
}: AddLessonsToSetModalProps) {
  const api = useApi();
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [busyLessonId, setBusyLessonId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const existingRoots = useMemo(
    () => new Set(lessonSet.lessons.map((lesson) => lesson.root_lesson_id)),
    [lessonSet.lessons],
  );
  const available = lessons.filter((lesson) => (
    lesson.status === 'ready' && !existingRoots.has(lesson.root_lesson_id)
  ));

  useEffect(() => {
    if (!isOpen) return;
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    listLessons(api, {}, controller.signal)
      .then(setLessons)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load lessons.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, isOpen]);

  async function add(lesson: LessonListItem) {
    try {
      setBusyLessonId(lesson.id);
      setError(null);
      onChange(await addLessonToSet(api, lessonSet.id, lesson.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to add lesson.');
    } finally {
      setBusyLessonId(null);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add lessons">
      <section className="text-left">
        {isLoading && <p className="py-5 text-center text-sm">Loading lessons…</p>}
        {!isLoading && available.length === 0 && (
          <p className="py-5 text-center text-sm">All ready lessons are already in this set.</p>
        )}
        <ul className="space-y-2">
          {available.map((lesson) => (
            <li key={lesson.id}>
              <button
                type="button"
                disabled={busyLessonId !== null}
                onClick={() => void add(lesson)}
                className="flex min-h-14 w-full items-center gap-3 rounded-lg border border-border bg-primary-bg px-3 py-2 text-left hover:border-accent disabled:opacity-50"
              >
                <LessonFormatIcon format={lesson.format} />
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-primary-text">{lesson.topic}</span>
                <Plus size={17} className="shrink-0 text-accent" />
              </button>
            </li>
          ))}
        </ul>
        {error && <p className="mt-4 rounded-lg bg-red-950/40 p-3 text-sm text-red-300">{error}</p>}
      </section>
    </Modal>
  );
}
