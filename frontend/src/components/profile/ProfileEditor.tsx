'use client';

import { useClerk, useUser } from '@clerk/nextjs';
import { Settings } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import Button from '@/components/ui/Button';
import { ApiError } from '@/lib/api/client';
import { getMyProfile, updateMyProfile } from '@/lib/api/profiles';
import { useApi } from '@/lib/hooks/useApi';

const BIO_LIMIT = 500;

export default function ProfileEditor() {
  const api = useApi();
  const { openUserProfile } = useClerk();
  const { isLoaded, user } = useUser();
  const clerkDisplayName = useMemo(() => (
    user?.fullName?.trim()
    || user?.username?.trim()
    || user?.firstName?.trim()
    || 'Chalksmith creator'
  ), [user]);
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [profileId, setProfileId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !user) return;
    const controller = new AbortController();
    getMyProfile(api, controller.signal)
      .then((profile) => {
        setDisplayName(profile.display_name);
        setBio(profile.bio);
        setProfileId(profile.id);
      })
      .catch((caught) => {
        if (controller.signal.aborted) return;
        if (caught instanceof ApiError && caught.status === 404) {
          setDisplayName(clerkDisplayName);
          return;
        }
        setError(caught instanceof Error ? caught.message : 'Failed to load your profile.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, clerkDisplayName, isLoaded, user]);

  async function saveProfile() {
    const trimmedName = displayName.trim();
    if (!trimmedName) {
      setError('Enter a public display name.');
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await updateMyProfile(api, {
        displayName: trimmedName,
        bio,
      });
      setDisplayName(saved.display_name);
      setBio(saved.bio);
      setProfileId(saved.id);
      setMessage('Profile saved.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to save your profile.');
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <p className="text-secondary-text">Loading your profile…</p>;
  }

  return (
    <form className="grid gap-6" onSubmit={(event) => { event.preventDefault(); void saveProfile(); }}>
      <label className="grid gap-2 text-sm font-medium">
        Public display name
        <input
          value={displayName}
          maxLength={80}
          onChange={(event) => setDisplayName(event.target.value)}
          className="rounded-xl border border-border bg-secondary-bg px-4 py-3 text-primary-text outline-none transition-colors focus:border-accent"
          placeholder="Your name"
        />
      </label>

      <label className="grid gap-2 text-sm font-medium">
        About you
        <textarea
          value={bio}
          maxLength={BIO_LIMIT}
          rows={6}
          onChange={(event) => setBio(event.target.value)}
          className="resize-none rounded-xl border border-border bg-secondary-bg px-4 py-3 leading-6 text-primary-text outline-none transition-colors focus:border-accent"
          placeholder="Share a short introduction about yourself, what you teach, or what you enjoy creating."
        />
        <span className="text-right text-xs font-normal text-secondary-text">{bio.length}/{BIO_LIMIT}</span>
      </label>

      <p className="text-sm text-secondary-text">
        Your display name and introduction are public. Your email address is never included.
      </p>
      {error && <p className="text-sm text-red-300">{error}</p>}
      {message && <p className="text-sm text-emerald-300">{message}</p>}

      <section className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? 'Saving…' : 'Save profile'}
        </Button>
        <Button type="button" variant="outline" className="gap-2" onClick={() => openUserProfile()}>
          <Settings size={15} />
          Account settings
        </Button>
        {profileId && (
          <Link href={`/profile/${profileId}`} className="text-sm text-accent hover:text-amber-500">
            View public profile
          </Link>
        )}
      </section>
    </form>
  );
}
