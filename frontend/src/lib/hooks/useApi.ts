'use client';

import { useMemo } from 'react';

import { useAuth } from '@/components/auth/AuthProvider';
import { createApiClient } from '@/lib/api/client';

export function useApi() {
  const { getIdToken } = useAuth();
  return useMemo(() => createApiClient({ getAccessToken: getIdToken }), [getIdToken]);
}
