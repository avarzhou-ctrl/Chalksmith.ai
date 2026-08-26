import type { ApiClient } from '@/lib/api/client';
import type { PublicProfile } from '@/lib/types/api';

export function getMyProfile(client: ApiClient, signal?: AbortSignal) {
  return client.request<PublicProfile>('/v2/profile', { signal });
}

export function updateMyProfile(
  client: ApiClient,
  profile: { displayName: string; bio: string },
) {
  return client.request<PublicProfile>('/v2/profile', {
    method: 'PUT',
    body: JSON.stringify({
      display_name: profile.displayName,
      bio: profile.bio,
    }),
  });
}

export function getPublicProfile(
  client: ApiClient,
  profileId: string,
  signal?: AbortSignal,
) {
  return client.request<PublicProfile>(`/v2/profiles/${profileId}`, { signal });
}
