'use client';

import Link from 'next/link';
import { SignUpButton, UserButton, useAuth } from '@clerk/nextjs';
import { LogIn, UserRound } from 'lucide-react';
import { generationHref } from '@/lib/navigation';

export function AuthButton() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <Link
        href={generationHref}
        aria-label="Start Free"
        className="grid size-10 shrink-0 place-items-center rounded-lg bg-amber-600 text-sm font-medium text-stone-950 hover:bg-amber-500 sm:flex sm:size-auto sm:gap-2 sm:px-4 sm:py-2"
      >
        <span className="hidden sm:inline">Start Free</span>
        <LogIn className="size-4" />
      </Link>
    );
  }
  if (isSignedIn) {
    return (
      <UserButton
        appearance={{
          elements: {
            userButtonAvatarBox: 'size-10',
            userButtonTrigger: 'size-10',
            userButtonPopoverActionButton: '!text-stone-50 hover:!bg-stone-700',
            userButtonPopoverActionButtonIcon: '!text-stone-400',
            userButtonPopoverCustomItemButton: '!text-stone-50 hover:!bg-stone-700',
            userButtonPopoverCustomItemButtonIconBox: '!text-stone-400',
            userButtonPopoverActionItemButtonIcon: '!text-stone-400',
          },
        }}
      >
        <UserButton.MenuItems>
          <UserButton.Link
            label="Public profile"
            href="/profile"
            labelIcon={<UserRound size={16} />}
          />
        </UserButton.MenuItems>
      </UserButton>
    );
  }

  return (
    <SignUpButton mode="modal" forceRedirectUrl={generationHref} signInForceRedirectUrl={generationHref}>
      <button type="button" aria-label="Start Free" className="grid size-10 shrink-0 place-items-center rounded-lg bg-amber-600 text-sm font-medium text-stone-950 hover:bg-amber-500 sm:flex sm:size-auto sm:gap-2 sm:px-4 sm:py-2">
        <span className="hidden sm:inline">Start Free</span>
        <LogIn className="size-4" />
      </button>
    </SignUpButton>
  );
}
