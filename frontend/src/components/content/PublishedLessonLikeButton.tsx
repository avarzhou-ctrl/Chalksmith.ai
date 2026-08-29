'use client';

import { SignInButton } from '@clerk/nextjs';
import { Heart } from 'lucide-react';

interface PublishedLessonLikeButtonProps {
  count: number;
  isLiked: boolean;
  isSignedIn: boolean;
  isBusy?: boolean;
  onToggle: () => void;
}

function LikeButton({
  count,
  isLiked,
  isBusy,
  onToggle,
}: Omit<PublishedLessonLikeButtonProps, 'isSignedIn'>) {
  const label = isLiked ? 'Unlike this lesson' : 'Like this lesson';

  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={isLiked}
      title={label}
      disabled={isBusy}
      onClick={onToggle}
      className={`inline-flex min-h-8 items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent disabled:cursor-wait disabled:opacity-60 ${
        isLiked
          ? 'border-accent/50 bg-accent/10 text-accent'
          : 'border-border text-secondary-text hover:border-accent hover:text-accent'
      }`}
    >
      <Heart size={14} fill={isLiked ? 'currentColor' : 'none'} aria-hidden="true" />
      <span>{count}</span>
    </button>
  );
}

export default function PublishedLessonLikeButton(props: PublishedLessonLikeButtonProps) {
  if (props.isSignedIn) {
    return <LikeButton {...props} />;
  }

  return (
    <SignInButton mode="modal">
      <span className="inline-flex">
        <LikeButton {...props} onToggle={() => undefined} />
      </span>
    </SignInButton>
  );
}
