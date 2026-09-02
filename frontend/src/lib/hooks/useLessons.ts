'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { deleteLesson, listLessons, moveLesson } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import { LESSON_MOVED_EVENT, type LessonMovedDetail } from '@/lib/lesson-drag';
import type { LessonFormat, LessonListItem } from '@/lib/types/api';

interface LessonFilters {
  q?: string;
  format?: LessonFormat;
  tags?: string[];
  folderId?: string | null;
}

export function useLessons(filters: LessonFilters = {}, debounceMs = 0) {
  const api = useApi();
  const [lessons, setLessons] = useState<LessonListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const loadMoreControllerRef = useRef<AbortController | null>(null);
  const { q, format, tags, folderId } = filters;
  const tagKey = tags?.join('\u0000') ?? '';
  const requestTags = tagKey ? tagKey.split('\u0000') : undefined;

  useEffect(() => {
    let isActive = true;
    const controller = new AbortController();
    loadMoreControllerRef.current?.abort();
    loadMoreControllerRef.current = null;
    setLessons([]);
    setNextCursor(null);
    setIsLoadingMore(false);
    setIsLoading(true);
    setError(null);

    const load = async () => {
      try {
        const page = await listLessons(
          api,
          { q, format, tags: requestTags, folderId },
          { signal: controller.signal },
        );
        if (isActive) {
          setLessons(page.items);
          setNextCursor(page.next_cursor);
        }
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
      loadMoreControllerRef.current?.abort();
      loadMoreControllerRef.current = null;
      window.clearTimeout(timeoutId);
    };
  }, [api, debounceMs, folderId, format, q, tagKey]);

  const loadMore = useCallback(async () => {
    if (!nextCursor || isLoading || isLoadingMore || loadMoreControllerRef.current) return;
    const controller = new AbortController();
    loadMoreControllerRef.current = controller;
    setIsLoadingMore(true);
    setError(null);
    try {
      const page = await listLessons(
        api,
        { q, format, tags: requestTags, folderId },
        { cursor: nextCursor, signal: controller.signal },
      );
      if (!controller.signal.aborted) {
        setLessons((current) => {
          const loadedIds = new Set(current.map((lesson) => lesson.id));
          return [...current, ...page.items.filter((lesson) => !loadedIds.has(lesson.id))];
        });
        setNextCursor(page.next_cursor);
      }
    } catch (caught) {
      if (!controller.signal.aborted) {
        setError(caught instanceof Error ? caught.message : 'Failed to load more lessons.');
      }
    } finally {
      if (loadMoreControllerRef.current === controller) {
        loadMoreControllerRef.current = null;
        setIsLoadingMore(false);
      }
    }
  }, [api, folderId, format, isLoading, isLoadingMore, nextCursor, q, tagKey]);

  const applyLessonMove = useCallback((lessonId: string, nextFolderId: string | null) => {
    setLessons((current) => {
      if (folderId !== undefined && folderId !== nextFolderId) {
        return current.filter((lesson) => lesson.id !== lessonId);
      }
      return current.map((lesson) => (
        lesson.id === lessonId ? { ...lesson, folder_id: nextFolderId } : lesson
      ));
    });
  }, [folderId]);

  useEffect(() => {
    const handleLessonMoved = (event: Event) => {
      const { lessonId, folderId } = (event as CustomEvent<LessonMovedDetail>).detail;
      applyLessonMove(lessonId, folderId);
    };
    window.addEventListener(LESSON_MOVED_EVENT, handleLessonMoved);
    return () => window.removeEventListener(LESSON_MOVED_EVENT, handleLessonMoved);
  }, [applyLessonMove]);

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
      applyLessonMove(lessonId, folderId);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Failed to move lesson.';
      setError(message);
      throw caught;
    }
  }, [api, applyLessonMove]);

  return {
    lessons,
    isLoading,
    isLoadingMore,
    hasMore: nextCursor !== null,
    error,
    loadMore,
    removeLesson,
    moveLessonToFolder,
  };
}
