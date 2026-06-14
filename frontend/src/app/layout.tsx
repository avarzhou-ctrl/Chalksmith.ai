// src/app/layout.tsx
import type { Metadata } from 'next'
import { ClerkProvider, Show, UserButton, SignUpButton } from '@clerk/nextjs'
import { LogIn } from 'lucide-react'
import { Inter } from 'next/font/google'
import './globals.css'

import Link from 'next/link'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'Chalksmith | Code-Driven STEM Animations',
  description: 'AI-powered tool for creating educational content.',
  metadataBase: new URL('https://chalksmith.ai'),
  icons: {
    icon: '/favicon.ico',
    apple: '/logo.png',
  },
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} bg-primary-bg text-primary-text antialiased`}>
        <ClerkProvider>
          <header
            data-site-header
            className="sticky top-0 z-50 mx-auto flex w-full max-w-7xl items-center justify-between border-b border-stone-800 bg-primary-bg/90 px-4 py-5 backdrop-blur sm:px-6 lg:px-8"
          >
            <Link href="/" className="flex items-center gap-3" aria-label="Chalksmith.ai home">
              <span className="grid size-10 place-items-center rounded-lg text-stone-950">
                <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain" />
              </span>
              <span className="hidden text-md font-semibold text-stone-50 sm:inline">Chalksmith.ai</span>
            </Link>
            <nav className="hidden items-center gap-10 text-sm font-medium text-stone-300 sm:flex">
              <a className="transition-colors hover:text-stone-50" href="#content">
                Content
              </a>
              <a className="transition-colors hover:text-stone-50" href="#about">
                About us
              </a>
            </nav>

            { /* User Profile / Auth Button */ }
            <Show when="signed-in">
              <UserButton 
                appearance={{
                  elements: {
                    userButtonAvatarBox: "h-12 w-12", 
                    userButtonTrigger: "h-12 w-12"
                  },
                }} 
              />
            </Show>

            <Show when="signed-out">
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
            </Show>
          </header>
          {children}
        </ClerkProvider>
      </body>
    </html>
  )
}
