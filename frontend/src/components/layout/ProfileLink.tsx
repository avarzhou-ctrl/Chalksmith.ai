'use client'

import { useUser } from '@clerk/nextjs'
import { UserRound } from 'lucide-react'
import Link from 'next/link'

export default function ProfileLink() {
  const { user } = useUser()

  return (
    <Link
      href="/dashboard"
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
