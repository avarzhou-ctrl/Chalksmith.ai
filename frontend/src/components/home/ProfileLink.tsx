'use client'

import { useEffect, useRef } from 'react'
import { SignUpButton, useUser } from '@clerk/nextjs'
import { LogIn, UserRound } from 'lucide-react'
import Link from 'next/link'

const AUTH_REFRESH_KEY = 'chalksmith-home-auth-refresh-at'
const AUTH_REFRESH_COOLDOWN_MS = 3000

function reloadForFreshAuthState() {
  const lastRefresh = Number(window.sessionStorage.getItem(AUTH_REFRESH_KEY) || 0)

  if (Date.now() - lastRefresh < AUTH_REFRESH_COOLDOWN_MS) {
    return
  }

  window.sessionStorage.setItem(AUTH_REFRESH_KEY, String(Date.now()))
  window.location.reload()
}

export default function ProfileLink() {
  const { isLoaded, isSignedIn, user } = useUser()
  const wasHiddenRef = useRef(false)

  useEffect(() => {
    if (!isLoaded) {
      return
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        wasHiddenRef.current = true
        return
      }

      if (wasHiddenRef.current) {
        reloadForFreshAuthState()
      }
    }

    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) { // User pressed Back or Forward key
        reloadForFreshAuthState() // Hard refresh
      }
    }

    window.addEventListener('focus', reloadForFreshAuthState)
    window.addEventListener('pageshow', handlePageShow)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      window.removeEventListener('focus', reloadForFreshAuthState)
      window.removeEventListener('pageshow', handlePageShow)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [isLoaded])

  if (!isLoaded || !isSignedIn) {
    return (
      <SignUpButton
        mode="modal"
        forceRedirectUrl="https://app.chalksmith.ai"
        fallbackRedirectUrl="https://app.chalksmith.ai"
        signInForceRedirectUrl="https://app.chalksmith.ai"
        signInFallbackRedirectUrl="https://app.chalksmith.ai"
      >
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
