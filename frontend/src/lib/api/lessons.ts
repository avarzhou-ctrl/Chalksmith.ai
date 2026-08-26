import type { ApiClient } from '@/lib/api/client';
import type {
  AccessUrl,
  FinalLessonSelection,
  Lesson,
  LessonFormat,
  LessonListItem,
  LessonPublication,
  LessonVersion,
} from '@/lib/types/api';

export function listLessons(
  client: ApiClient,
  filters: { q?: string; format?: LessonFormat } = {},
  signal?: AbortSignal,
) {
  const query = new URLSearchParams();
  if (filters.q) query.set('q', filters.q);
  if (filters.format) query.set('format', filters.format);
  const suffix = query.size ? `?${query}` : '';
  return client.request<LessonListItem[]>(`/v2/lessons${suffix}`, { signal });
}

export function getLesson(client: ApiClient, lessonId: string, signal?: AbortSignal) {
  return client.request<Lesson>(`/v2/lessons/${lessonId}`, { signal });
}

export function getLessonVersions(client: ApiClient, lessonId: string, signal?: AbortSignal) {
  return client.request<LessonVersion[]>(`/v2/lessons/${lessonId}/versions`, { signal });
}

export function renameLesson(client: ApiClient, lessonId: string, topic: string) {
  return client.request<Lesson>(`/v2/lessons/${lessonId}`, {
    method: 'PATCH',
    body: JSON.stringify({ topic }),
  });
}

export function deleteLesson(client: ApiClient, lessonId: string) {
  return client.request<void>(`/v2/lessons/${lessonId}`, { method: 'DELETE' });
}

export function selectFinalLesson(client: ApiClient, lessonId: string) {
  return client.request<FinalLessonSelection>(`/v2/lessons/${lessonId}/final`, {
    method: 'PUT',
  });
}

export function setLessonPublication(
  client: ApiClient,
  lessonId: string,
  published: boolean,
  displayName?: string,
) {
  return client.request<LessonPublication>(`/v2/lessons/${lessonId}/publication`, {
    method: 'PUT',
    body: JSON.stringify({
      published,
      ...(published && displayName ? { display_name: displayName } : {}),
    }),
  });
}

export function getLessonAccessUrl(
  client: ApiClient,
  lessonId: string,
  download = false,
  signal?: AbortSignal,
) {
  return client.request<AccessUrl>(`/v2/lessons/${lessonId}/access-url?download=${download}`, {
    method: 'POST',
    signal,
  });
}
