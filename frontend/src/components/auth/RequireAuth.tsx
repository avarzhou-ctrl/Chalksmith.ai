'use client';

import { useEffect, type ReactNode } from 'react';

import { useAuth } from '@/components/auth/AuthProvider';

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading, openAuth } = useAuth();
  useEffect(() => {
    if (!loading && !user) openAuth();
  }, [loading, openAuth, user]);
  if (loading) return <main className="grid min-h-screen place-items-center bg-stone-950 text-stone-400">Loading session…</main>;
  if (!user) return <main className="grid min-h-screen place-items-center bg-stone-950 text-stone-400">Sign in to continue.</main>;
  return children;
}
