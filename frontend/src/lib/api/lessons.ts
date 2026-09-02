import type { ApiClient } from '@/lib/api/client';
import type {
  AccessUrl,
  FinalLessonSelection,
  Lesson,
  LessonFormat,
  LessonListPage,
  LessonPublication,
  LessonTags,
  LessonTagItem,
  LessonVersion,
} from '@/lib/types/api';

interface LessonFilters {
  q?: string;
  format?: LessonFormat;
  tags?: string[];
}

interface LessonPageFilters extends LessonFilters {
  folderId?: string | null;
}

function lessonQuery(filters: LessonFilters) {
  const query = new URLSearchParams();
  if (filters.q) query.set('q', filters.q);
  if (filters.format) query.set('format', filters.format);
  filters.tags?.forEach((tag) => query.append('tag', tag));
  return query;
}

export function listLessons(
  client: ApiClient,
  filters: LessonPageFilters = {},
  options: { cursor?: string; pageSize?: number; signal?: AbortSignal } = {},
) {
  const query = lessonQuery(filters);
  if (filters.folderId !== undefined) {
    query.set('folder_id', filters.folderId ?? 'root');
  }
  if (options.cursor) query.set('cursor', options.cursor);
  query.set('page_size', String(options.pageSize ?? 24));
  return client.request<LessonListPage>(`/v2/lessons?${query}`, { signal: options.signal });
}

export function getLesson(client: ApiClient, lessonId: string, signal?: AbortSignal) {
  return client.request<Lesson>(`/v2/lessons/${lessonId}`, { signal });
}

export function listLessonTags(client: ApiClient, signal?: AbortSignal) {
  return client.request<LessonTagItem[]>('/v2/lessons/tags', { signal });
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

export function moveLesson(client: ApiClient, lessonId: string, folderId: string | null) {
  return client.request<Lesson>(`/v2/lessons/${lessonId}/folder`, {
    method: 'PUT',
    body: JSON.stringify({ folder_id: folderId }),
  });
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

export function setLessonTags(client: ApiClient, lessonId: string, tags: string[]) {
  return client.request<LessonTags>(`/v2/lessons/${lessonId}/tags`, {
    method: 'PUT',
    body: JSON.stringify({ tags }),
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
