import type { ApiClient } from '@/lib/api/client';
import type {
  AccessUrl,
  LessonFormat,
  PublishedLessonItem,
  PublishedLessonLikeResponse,
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

export function listMyPublishedLessons(client: ApiClient, signal?: AbortSignal) {
  return client.request<PublishedLessonItem[]>('/v2/explore/lessons/mine', { signal });
}

export function listPublishedTags(client: ApiClient, signal?: AbortSignal) {
  return client.request<PublishedTagItem[]>('/v2/explore/tags', { signal });
}

export function getPublishedLesson(
  client: ApiClient,
  lessonId: string,
  signal?: AbortSignal,
) {
  return client.request<PublishedLessonItem>(`/v2/explore/lessons/${lessonId}`, { signal });
}

export function listLikedPublishedLessonIds(
  client: ApiClient,
  rootLessonIds: string[],
  signal?: AbortSignal,
) {
  const query = new URLSearchParams();
  rootLessonIds.forEach((rootId) => query.append('root_id', rootId));
  const suffix = query.size ? `?${query}` : '';
  return client.request<string[]>(`/v2/explore/lessons/liked${suffix}`, { signal });
}

export function setPublishedLessonLike(
  client: ApiClient,
  lessonId: string,
  liked: boolean,
) {
  return client.request<PublishedLessonLikeResponse>(
    `/v2/explore/lessons/${lessonId}/like`,
    { method: liked ? 'PUT' : 'DELETE' },
  );
}

export function getPublishedLessonAccessUrl(
  client: ApiClient,
  lessonId: string,
  download = false,
  signal?: AbortSignal,
) {
  return client.request<AccessUrl>(
    `/v2/explore/lessons/${lessonId}/access-url?download=${download}`,
    { method: 'POST', signal },
  );
}
