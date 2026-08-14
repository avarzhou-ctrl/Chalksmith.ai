'use client';

import { useCallback, useEffect, useState } from 'react';

import { deleteLesson, listLessons } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonFormat, LessonListItem } from '@/lib/types/api';

interface LessonFilters {
  q?: string;
  format?: LessonFormat;
}

export function useLessons(filters: LessonFilters = {}, debounceMs = 0) {
  const api = useApi();
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { q, format } = filters;

  useEffect(() => {
    let isActive = true;
    const controller = new AbortController();

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await listLessons(api, { q, format }, controller.signal);
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
  }, [api, debounceMs, format, q]);

  const removeLesson = useCallback(async (lessonId: string) => {
    try {
      setError(null);
      await deleteLesson(api, lessonId);
      setLessons((current) => current.filter((lesson) => lesson.id !== lessonId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to delete lesson.');
    }
  }, [api]);

  return { lessons, isLoading, error, removeLesson };
}
