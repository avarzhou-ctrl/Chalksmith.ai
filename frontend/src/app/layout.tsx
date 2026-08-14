// src/app/layout.tsx
import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

import Link from 'next/link'
import { AuthButton } from '@/components/auth/AuthButton'

const configuredDomain = process.env.NEXT_PUBLIC_SITE_DOMAIN
const siteDomain = configuredDomain || 'chalksmith.ai'
// The app host has to cross back to the marketing site, which a relative href
// cannot do. Unset means local development, where relative is the right answer.
const homeHref = configuredDomain ? `https://${configuredDomain}/` : '/'

export const metadata: Metadata = {
  title: 'Chalksmith | Code-Driven STEM Animations',
  description: 'An AI-driven tool for generating code-driven educational STEM animations from natural language.',
  metadataBase: new URL(`https://${siteDomain}`),
  icons: {
    icon: '/favicon.ico',
    apple: '/logo.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="bg-primary-bg text-primary-text antialiased">
        <ClerkProvider>
          <header
            data-site-header
            className="sticky top-0 z-50 mx-auto flex w-full max-w-7xl items-center justify-between border-b border-stone-800 bg-primary-bg/90 px-4 py-5 backdrop-blur sm:px-6 lg:px-8"
          >
            <Link href={homeHref} className="flex items-center gap-3" aria-label="Chalksmith.ai home">
              <span className="grid size-10 place-items-center rounded-lg text-stone-950">
                <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain" />
              </span>
              <span className="hidden text-md font-semibold text-stone-50 sm:inline">Chalksmith.ai</span>
            </Link>
            <nav className="hidden items-center gap-10 text-sm font-medium text-stone-300 sm:flex">
              <Link className="transition-colors hover:text-stone-50" href="/dashboard">
                Dashboard
              </Link>
              <Link className="transition-colors hover:text-stone-50" href="/content">
                Explore
              </Link>
              <Link className="transition-colors hover:text-stone-50" href="/about">
                About Us
              </Link>
            </nav>

            <AuthButton />
          </header>
          {children}
        </ClerkProvider>
      </body>
    </html>
  )
}
