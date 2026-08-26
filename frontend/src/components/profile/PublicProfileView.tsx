'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { UserRound } from 'lucide-react';

import { createPublicApiClient } from '@/lib/api/client';
import { getPublicProfile } from '@/lib/api/profiles';
import type { PublicProfile } from '@/lib/types/api';

export default function PublicProfileView({ profileId }: { profileId: string }) {
  const api = useMemo(() => createPublicApiClient(), []);
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getPublicProfile(api, profileId, controller.signal)
      .then(setProfile)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Profile not found.');
        }
      });
    return () => controller.abort();
  }, [api, profileId]);

  if (error) return <p className="text-center text-red-300">{error}</p>;
  if (!profile) return <p className="text-center text-secondary-text">Loading profile…</p>;

  return (
    <article className="rounded-3xl border border-border bg-secondary-bg p-8 shadow-xl shadow-stone-950/20 sm:p-10">
      <span className="grid size-14 place-items-center rounded-2xl bg-accent/10 text-accent">
        <UserRound className="size-7" aria-hidden />
      </span>
      <h1 className="mt-6 text-3xl font-bold tracking-tight">{profile.display_name}</h1>
      <p className="mt-5 whitespace-pre-wrap leading-7 text-secondary-text">
        {profile.bio || 'This creator has not added an introduction yet.'}
      </p>
      <Link href="/content" className="mt-8 inline-block text-sm font-medium text-accent hover:text-amber-500">
        Explore published lessons
      </Link>
    </article>
  );
}
