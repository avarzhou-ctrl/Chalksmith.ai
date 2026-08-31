'use client';

import { useCallback, useEffect, useState } from 'react';

import { deleteLesson, listLessons, moveLesson } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import { LESSON_MOVED_EVENT, type LessonMovedDetail } from '@/lib/lesson-drag';
import type { LessonFormat, LessonListItem } from '@/lib/types/api';

interface LessonFilters {
  q?: string;
  format?: LessonFormat;
  tags?: string[];
}

export function useLessons(filters: LessonFilters = {}, debounceMs = 0) {
  const api = useApi();
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { q, format, tags } = filters;
  const tagKey = tags?.join('\u0000') ?? '';

  useEffect(() => {
    let isActive = true;
    const controller = new AbortController();

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listLessons(api, { q, format, tags }, controller.signal);
        if (isActive) setLessons(data);
      } catch (caught) {
        if (isActive && !controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load lessons.');
        }
      } finally {
        if (isActive) setIsLoading(false);
      }
    };

    const timeoutId = window.setTimeout(() => void load(), debounceMs);
    return () => {
      isActive = false;
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [api, debounceMs, format, q, tagKey]);

  useEffect(() => {
    const recordMove = (event: Event) => {
      const { lessonId, folderId } = (event as CustomEvent<LessonMovedDetail>).detail;
      setLessons((current) => current.map((lesson) => (
        lesson.id === lessonId ? { ...lesson, folder_id: folderId } : lesson
      )));
    };
    window.addEventListener(LESSON_MOVED_EVENT, recordMove);
    return () => window.removeEventListener(LESSON_MOVED_EVENT, recordMove);
  }, []);

  const removeLesson = useCallback(async (lessonId: string) => {
    try {
      setError(null);
      await deleteLesson(api, lessonId);
      setLessons((current) => current.filter((lesson) => lesson.id !== lessonId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to delete lesson.');
    }
  }, [api]);

  const moveLessonToFolder = useCallback(async (lessonId: string, folderId: string | null) => {
    try {
      setError(null);
      await moveLesson(api, lessonId, folderId);
      setLessons((current) => current.map((lesson) => (
        lesson.id === lessonId ? { ...lesson, folder_id: folderId } : lesson
      )));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Failed to move lesson.';
      setError(message);
      throw caught;
    }
  }, [api]);

  return { lessons, isLoading, error, removeLesson, moveLessonToFolder };
}
