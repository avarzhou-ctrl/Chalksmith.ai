import type { ApiClient } from '@/lib/api/client';
import type {
  AccessUrl,
  LessonFormat,
  PublishedLessonItem,
  PublishedTagItem,
} from '@/lib/types/api';

export function listPublishedLessons(
  client: ApiClient,
  filters: { q?: string; format?: LessonFormat; tags?: string[] } = {},
  signal?: AbortSignal,
) {
  const query = new URLSearchParams();
  if (filters.q) query.set('q', filters.q);
  if (filters.format) query.set('format', filters.format);
  filters.tags?.forEach((tag) => query.append('tag', tag));
  const suffix = query.size ? `?${query}` : '';
  return client.request<PublishedLessonItem[]>(`/v2/explore/lessons${suffix}`, { signal });
}

export function listPublishedTags(client: ApiClient, signal?: AbortSignal) {
  return client.request<PublishedTagItem[]>('/v2/explore/tags', { signal });
}

export function getPublishedLessonAccessUrl(
  client: ApiClient,
  lessonId: string,
  download = false,
) {
  return client.request<AccessUrl>(
    `/v2/explore/lessons/${lessonId}/access-url?download=${download}`,
    { method: 'POST' },
  );
}
