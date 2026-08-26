import type { ApiClient } from '@/lib/api/client';
import type { AccessUrl, PublishedLessonItem } from '@/lib/types/api';

export function listPublishedLessons(client: ApiClient, signal?: AbortSignal) {
  return client.request<PublishedLessonItem[]>('/v2/explore/lessons', { signal });
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
