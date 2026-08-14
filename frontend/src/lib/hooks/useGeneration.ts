'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import { streamGeneration } from '@/lib/api/generation-stream';
import { getLesson, getLessonAccessUrl, getLessonVersions, renameLesson } from '@/lib/api/lessons';
import type { ApiClient } from '@/lib/api/client';
import type { Lesson, LessonFormat, LessonVersion } from '@/lib/types/api';

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
  lessonId?: string;
  versionNumber?: number;
}

function messagesForVersions(versions: LessonVersion[]): GenerationMessage[] {
  return versions.flatMap((version) => [
    {
      role: 'user' as const,
      lessonId: version.id,
      versionNumber: version.version_number,
      content: version.edit_instruction
        || (version.version_number === 1
          ? `Create a lesson about “${version.topic}”.`
          : `Saved revision ${version.version_number}.`),
    },
    {
      role: 'assistant' as const,
      lessonId: version.id,
      versionNumber: version.version_number,
      content: version.summary || `Version ${version.version_number} is still being generated.`,
    },
  ]);
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
  const loadAbortRef = useRef<AbortController | null>(null);
  const previewCacheRef = useRef(new Map<string, { url: string; expiresAt: number }>());

  useEffect(() => () => {
    abortRef.current?.abort();
    loadAbortRef.current?.abort();
  }, []);

  const loadLesson = useCallback(async (lessonId: string, refreshVersions = true) => {
    loadAbortRef.current?.abort();
    const controller = new AbortController();
    loadAbortRef.current = controller;
    setLoading(true);
    setProgress(0);
    setStatus('Loading lesson…');
    setError(null);
    setPreviewUrl('');
    try {
      const [saved, versions] = await Promise.all([
        getLesson(api, lessonId, controller.signal),
        refreshVersions
          ? getLessonVersions(api, lessonId, controller.signal)
          : Promise.resolve(null),
      ]);
      if (controller.signal.aborted) return false;
      setLesson(saved);
      setTitle(saved.topic);
      setOriginalTopic(saved.topic);
      setFormat(saved.format);
      if (versions) setMessages(messagesForVersions(versions));
      if (saved.status === 'ready') {
        const cachedPreview = previewCacheRef.current.get(saved.id);
        if (cachedPreview && cachedPreview.expiresAt > Date.now() + 30_000) {
          setPreviewUrl(cachedPreview.url);
        } else {
          const access = await getLessonAccessUrl(api, saved.id, false, controller.signal);
          if (controller.signal.aborted) return false;
          previewCacheRef.current.set(saved.id, {
            url: access.url,
            expiresAt: Date.now() + access.expires_in * 1000,
          });
          setPreviewUrl(access.url);
        }
      } else if (saved.status === 'failed') {
        setError(saved.error_message || 'Lesson generation failed.');
      } else if (saved.status === 'deleting') {
        setError('This lesson is pending deletion.');
      } else {
        setError('This lesson is still being generated.');
      }
      return true;
    } catch (caught) {
      if (!controller.signal.aborted) {
        setError(caught instanceof Error ? caught.message : 'Failed to load lesson.');
      }
      return false;
    } finally {
      if (loadAbortRef.current === controller) {
        loadAbortRef.current = null;
        setLoading(false);
        setStatus(null);
      }
    }
  }, [api]);

  const selectLessonVersion = useCallback(async (lessonId: string) => {
    if (await loadLesson(lessonId, false)) {
      window.history.replaceState({}, '', `?lessonId=${lessonId}`);
    }
  }, [loadLesson]);

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
    setStatus(null);
  }, []);

  const startNewLesson = useCallback(() => {
    loadAbortRef.current?.abort();
    loadAbortRef.current = null;
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
            const baseProgress = PROGRESS[event.stage] ?? 50;
            if (
              event.generated_characters
              && (event.stage === 'generating' || event.stage === 'repairing')
            ) {
              const streamedProgress = Math.floor(event.generated_characters / 750);
              const progressLimit = event.stage === 'generating' ? 54 : 90;
              setProgress(Math.min(progressLimit, baseProgress + streamedProgress));
            } else {
              setProgress(baseProgress);
            }
          }
          if (event.type === 'complete') completedId = event.lesson_id;
          if (event.type === 'error') streamError = event.message;
        },
      });
      if (streamError) throw new Error(streamError);
      if (!completedId) throw new Error('Generation ended without a completed lesson.');

      await loadLesson(completedId);
      setTopic('');
      setSourceFiles([]);
      setProgress(100);
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
  }, [api, format, lesson, loadLesson, loading, originalTopic, sourceFiles, topic]);

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
    selectLessonVersion,
    stopGeneration,
    startNewLesson,
    generateLesson,
    updateTitle,
    downloadLesson,
  };
}
