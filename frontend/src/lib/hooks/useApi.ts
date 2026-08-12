'use client';

import { useAuth } from '@clerk/nextjs';
import { useCallback, useMemo } from 'react';

import { createApiClient } from '@/lib/api/client';

export function useApi() {
  const { getToken } = useAuth();
  const getAccessToken = useCallback(
    (forceRefresh = false) => getToken({ skipCache: forceRefresh }),
    [getToken],
  );

  return useMemo(() => createApiClient({ getAccessToken }), [getAccessToken]);
}
