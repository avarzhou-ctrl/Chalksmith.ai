'use client';

import { SignInButton, useAuth } from '@clerk/nextjs';
import { LogIn } from 'lucide-react';
import type { ReactNode } from 'react';

export function RequireAuth({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return fallback ?? <main className="grid min-h-screen place-items-center bg-stone-950 text-stone-400">Loading session…</main>;
  }
  if (!isSignedIn) {
    return (
      <main className="grid min-h-screen place-items-center bg-stone-950 p-6 text-stone-100">
        <section className="grid max-w-sm gap-4 text-center">
          <h1 className="text-2xl font-semibold">Sign in to continue</h1>
          <p className="text-sm text-stone-400">Your lessons are private and tied to your Chalksmith account.</p>
          <SignInButton mode="modal" forceRedirectUrl="/generation" signUpForceRedirectUrl="/generation">
            <button type="button" className="mx-auto flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 font-medium text-stone-950 hover:bg-amber-500">
              Sign in
              <LogIn className="size-4" />
            </button>
          </SignInButton>
        </section>
      </main>
    );
  }
  return children;
}
