'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { streamGeneration } from '@/lib/api/generation-stream';
import { getLesson, getLessonAccessUrl, renameLesson } from '@/lib/api/lessons';
import type { ApiClient } from '@/lib/api/client';
import type { Lesson, LessonFormat } from '@/lib/types/api';

const PROGRESS: Record<string, number> = {
  generating: 35,
  validating: 55,
  rendering: 70,
  repairing: 80,
  saving: 95,
};

export interface GenerationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function useGeneration(api: ApiClient) {
  const [topic, setTopic] = useState('');
  const [originalTopic, setOriginalTopic] = useState('');
  const [format, setFormat] = useState<LessonFormat | ''>('');
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [title, setTitle] = useState('Untitled');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [showCode, setShowCode] = useState(false);
  const [sourceFiles, setSourceFiles] = useState<File[]>([]);
  const [messages, setMessages] = useState<GenerationMessage[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const loadLesson = useCallback(async (lessonId: string) => {
    setLoading(true);
    setError(null);
    try {
      const saved = await getLesson(api, lessonId);
      setLesson(saved);
      setTitle(saved.topic);
      setOriginalTopic(saved.topic);
      setFormat(saved.format);
      setMessages([{ role: 'assistant', content: saved.summary || `Loaded “${saved.topic}”.` }]);
      if (saved.status === 'ready') {
        setPreviewUrl((await getLessonAccessUrl(api, saved.id)).url);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load lesson.');
    } finally {
      setLoading(false);
    }
  }, [api]);

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
    setStatus(null);
  }, []);

  const startNewLesson = useCallback(() => {
    stopGeneration();
    setTopic('');
    setOriginalTopic('');
    setFormat('');
    setLesson(null);
    setPreviewUrl('');
    setTitle('Untitled');
    setMessages([]);
    setSourceFiles([]);
    setError(null);
    setShowCode(false);
    window.history.replaceState({}, '', window.location.pathname);
  }, [stopGeneration]);

  const generateLesson = useCallback(async () => {
    const prompt = topic.trim();
    if (!prompt || !format || loading) return;

    let completedId = '';
    let streamError = '';
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    setShowCode(false);
    setProgress(10);
    setStatus('Starting generation…');
    setMessages((current) => [...current, { role: 'user', content: prompt }]);

    try {
      await streamGeneration({
        client: api,
        request: {
          topic: lesson ? originalTopic : prompt,
          format,
          baseLessonId: lesson?.id,
          editInstruction: lesson ? prompt : undefined,
          sourceFiles,
        },
        signal: controller.signal,
        onEvent: (event) => {
          if (event.type === 'progress') {
            setStatus(event.message);
            setProgress(PROGRESS[event.stage] ?? 50);
          }
          if (event.type === 'complete') completedId = event.lesson_id;
          if (event.type === 'error') streamError = event.message;
        },
      });
      if (streamError) throw new Error(streamError);
      if (!completedId) throw new Error('Generation ended without a completed lesson.');

      const completed = await getLesson(api, completedId);
      const access = await getLessonAccessUrl(api, completedId);
      setLesson(completed);
      setPreviewUrl(access.url);
      setTitle(completed.topic);
      setOriginalTopic(completed.topic);
      setTopic('');
      setSourceFiles([]);
      setProgress(100);
      setMessages((current) => [...current, {
        role: 'assistant',
        content: completed.summary || 'Lesson created successfully.',
      }]);
      window.history.replaceState({}, '', `?lessonId=${completedId}`);
    } catch (caught) {
      if (!controller.signal.aborted) {
        const message = caught instanceof Error ? caught.message : 'Lesson generation failed.';
        setError(message);
        setMessages((current) => [...current, { role: 'assistant', content: `Error: ${message}` }]);
      }
    } finally {
      setLoading(false);
      setStatus(null);
      abortRef.current = null;
    }
  }, [api, format, lesson, loading, originalTopic, sourceFiles, topic]);

  const updateTitle = useCallback(async (nextTitle: string) => {
    const trimmed = nextTitle.trim();
    if (!trimmed) return;
    try {
      if (lesson) await renameLesson(api, lesson.id, trimmed);
      setTitle(trimmed);
      setOriginalTopic(trimmed);
      setLesson((current) => current ? { ...current, topic: trimmed } : current);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to rename lesson.');
    }
  }, [api, lesson]);

  const downloadLesson = useCallback(async () => {
    if (!lesson) return;
    try {
      const access = await getLessonAccessUrl(api, lesson.id, true);
      window.location.assign(access.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to export lesson.');
    }
  }, [api, lesson]);

  return {
    topic,
    setTopic,
    format,
    setFormat,
    lesson,
    previewUrl,
    title,
    loading,
    status,
    progress,
    error,
    showCode,
    setShowCode,
    sourceFiles,
    setSourceFiles,
    messages,
    loadLesson,
    stopGeneration,
    startNewLesson,
    generateLesson,
    updateTitle,
    downloadLesson,
  };
}
