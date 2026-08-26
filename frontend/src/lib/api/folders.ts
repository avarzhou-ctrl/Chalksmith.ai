import type { ApiClient } from '@/lib/api/client';
import type { LessonFolder } from '@/lib/types/api';

export function listFolders(client: ApiClient, signal?: AbortSignal) {
  return client.request<LessonFolder[]>('/v2/folders', { signal });
}

export function createFolder(client: ApiClient, name: string, parentId: string | null) {
  return client.request<LessonFolder>('/v2/folders', {
    method: 'POST',
    body: JSON.stringify({ name, parent_id: parentId }),
  });
}

export function renameFolder(client: ApiClient, folderId: string, name: string) {
  return client.request<LessonFolder>(`/v2/folders/${folderId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
}

export function deleteFolder(client: ApiClient, folderId: string) {
  return client.request<void>(`/v2/folders/${folderId}`, { method: 'DELETE' });
}
