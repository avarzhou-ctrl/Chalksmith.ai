import type { ApiClient } from '@/lib/api/client';
import type { LessonSetDetail, LessonSetListItem } from '@/lib/types/api';

export function listLessonSets(client: ApiClient, signal?: AbortSignal) {
  return client.request<LessonSetListItem[]>('/v2/lesson-sets', { signal });
}

export function createLessonSet(client: ApiClient, title: string, description = '') {
  return client.request<LessonSetDetail>('/v2/lesson-sets', {
    method: 'POST',
    body: JSON.stringify({ title, description }),
  });
}

export function getLessonSet(client: ApiClient, lessonSetId: string, signal?: AbortSignal) {
  return client.request<LessonSetDetail>(`/v2/lesson-sets/${lessonSetId}`, { signal });
}

export function updateLessonSet(
  client: ApiClient,
  lessonSetId: string,
  update: { title?: string; description?: string },
) {
  return client.request<LessonSetDetail>(`/v2/lesson-sets/${lessonSetId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  });
}

export function deleteLessonSet(client: ApiClient, lessonSetId: string) {
  return client.request<void>(`/v2/lesson-sets/${lessonSetId}`, { method: 'DELETE' });
}

export function addLessonToSet(client: ApiClient, lessonSetId: string, lessonId: string) {
  return client.request<LessonSetDetail>(`/v2/lesson-sets/${lessonSetId}/lessons`, {
    method: 'POST',
    body: JSON.stringify({ lesson_id: lessonId }),
  });
}

export function removeLessonFromSet(
  client: ApiClient,
  lessonSetId: string,
  rootLessonId: string,
) {
  return client.request<LessonSetDetail>(
    `/v2/lesson-sets/${lessonSetId}/lessons/${rootLessonId}`,
    { method: 'DELETE' },
  );
}

export function reorderLessonSet(
  client: ApiClient,
  lessonSetId: string,
  rootLessonIds: string[],
) {
  return client.request<LessonSetDetail>(`/v2/lesson-sets/${lessonSetId}/order`, {
    method: 'PUT',
    body: JSON.stringify({ root_lesson_ids: rootLessonIds }),
  });
}
