'use client';

import { useEffect, useState } from 'react';

import type { ApiClient } from '@/lib/api/client';
import { getMyProfile } from '@/lib/api/profiles';

export function usePublicDisplayName(
  api: ApiClient,
  fallbackName: string,
  enabled: boolean,
) {
  const [displayName, setDisplayName] = useState(fallbackName);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!enabled) {
      setDisplayName(fallbackName);
      return;
    }
    const controller = new AbortController();
    setIsLoading(true);
    getMyProfile(api, controller.signal)
      .then((profile) => setDisplayName(profile.display_name))
      .catch(() => {
        if (!controller.signal.aborted) setDisplayName(fallbackName);
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, enabled, fallbackName]);

  return { displayName, isLoading };
}
