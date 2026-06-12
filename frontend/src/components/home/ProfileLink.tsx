'use client'

import { SignUpButton, useUser } from '@clerk/nextjs'
import { LogIn, UserRound } from 'lucide-react'
import Link from 'next/link'

export default function ProfileLink() {
  const { isLoaded, isSignedIn, user } = useUser()

  if (!isLoaded || !isSignedIn) {
    return (
      <SignUpButton mode="modal">
        <button
          type="button"
          className="flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-primary-text transition-colors duration-300 hover:bg-amber-700"
        >
          Create Account
          <LogIn className="size-4" aria-hidden="true" />
        </button>
      </SignUpButton>
    )
  }

  return (
    <Link
      href="https://app.chalksmith.ai/home"
      className="grid size-10 place-items-center overflow-hidden rounded-full border border-stone-700 bg-stone-800 text-stone-200 transition-colors hover:border-accent hover:text-accent"
      aria-label="Open dashboard"
    >
      {user?.imageUrl ? (
        <img src={user.imageUrl} alt="" className="size-10 object-cover" />
      ) : (
        <UserRound className="size-5" aria-hidden="true" />
      )}
    </Link>
  )
}
