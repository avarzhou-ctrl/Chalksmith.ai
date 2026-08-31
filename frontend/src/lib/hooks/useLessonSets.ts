'use client';

import { useAuth } from '@clerk/nextjs';
import { useCallback, useEffect, useState } from 'react';

import {
  addLessonToSet as addLessonToSetRequest,
  createLessonSet as createLessonSetRequest,
  deleteLessonSet as deleteLessonSetRequest,
  listLessonSets,
} from '@/lib/api/lesson-sets';
import { useApi } from '@/lib/hooks/useApi';
import {
  dispatchLessonAddedToSet,
  dispatchLessonSetsChanged,
  LESSON_ADDED_TO_SET_EVENT,
  LESSON_SETS_CHANGED_EVENT,
} from '@/lib/lesson-drag';
import type { LessonSetListItem } from '@/lib/types/api';

export function useLessonSets() {
  const api = useApi();
  const { isLoaded, isSignedIn } = useAuth();
  const [lessonSets, setLessonSets] = useState<LessonSetListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) {
      setIsLoading(!isLoaded);
      return;
    }
    const controller = new AbortController();
    setIsLoading(true);
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
  }, [api, isLoaded, isSignedIn]);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    const syncLessonSets = () => {
      void listLessonSets(api)
        .then(setLessonSets)
        .catch((caught) => setError(caught instanceof Error ? caught.message : 'Failed to refresh lesson sets.'));
    };
    window.addEventListener(LESSON_ADDED_TO_SET_EVENT, syncLessonSets);
    window.addEventListener(LESSON_SETS_CHANGED_EVENT, syncLessonSets);
    return () => {
      window.removeEventListener(LESSON_ADDED_TO_SET_EVENT, syncLessonSets);
      window.removeEventListener(LESSON_SETS_CHANGED_EVENT, syncLessonSets);
    };
  }, [api, isLoaded, isSignedIn]);

  const createLessonSet = useCallback(async (title: string, description: string) => {
    setError(null);
    const created = await createLessonSetRequest(api, title, description);
    setLessonSets((current) => [{
      id: created.id,
      title: created.title,
      description: created.description,
      lesson_count: created.lessons.length,
      preview_lessons: created.lessons.slice(0, 3),
      created_at: created.created_at,
      updated_at: created.updated_at,
    }, ...current]);
    dispatchLessonSetsChanged();
    return created;
  }, [api]);

  const deleteLessonSet = useCallback(async (lessonSetId: string) => {
    setError(null);
    await deleteLessonSetRequest(api, lessonSetId);
    setLessonSets((current) => current.filter((lessonSet) => lessonSet.id !== lessonSetId));
    dispatchLessonSetsChanged();
  }, [api]);

  const addLessonToSet = useCallback(async (lessonSetId: string, lessonId: string) => {
    setError(null);
    const updated = await addLessonToSetRequest(api, lessonSetId, lessonId);
    setLessonSets((current) => current.map((lessonSet) => lessonSet.id === lessonSetId ? {
      ...lessonSet,
      lesson_count: updated.lessons.length,
      preview_lessons: updated.lessons.slice(0, 3),
      updated_at: updated.updated_at,
    } : lessonSet));
    dispatchLessonAddedToSet({ lessonId, lessonSetId });
    return updated;
  }, [api]);

  return { lessonSets, isLoading, error, createLessonSet, deleteLessonSet, addLessonToSet };
}
