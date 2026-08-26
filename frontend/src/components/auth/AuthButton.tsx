'use client';

import { SignUpButton, UserButton, useAuth } from '@clerk/nextjs';
import { LogIn, UserRound } from 'lucide-react';

export function AuthButton() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return <span className="size-10 animate-pulse rounded-full bg-stone-800" />;
  }
  if (isSignedIn) {
    return (
      <UserButton
        appearance={{
          elements: {
            userButtonAvatarBox: 'size-10',
            userButtonTrigger: 'size-10',
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
    <SignUpButton mode="modal" forceRedirectUrl="/generation" signInForceRedirectUrl="/generation">
      <button type="button" className="flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-stone-950 hover:bg-amber-500">
        Start Free
        <LogIn className="size-4" />
      </button>
    </SignUpButton>
  );
}
