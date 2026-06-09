// src/app/layout.tsx
import type { Metadata } from 'next'
import { ClerkProvider, Show, SignUpButton, UserButton } from '@clerk/nextjs'
import { Inter } from 'next/font/google'
import './globals.css'

import Link from 'next/link';
import { LogIn } from 'lucide-react';

function PrimaryCtaLink({ href, children, size = 'md' }: { href: string; children: React.ReactNode; size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <Link
      href={href}
      className={`flex items-center justify-center gap-2 rounded-lg bg-accent font-medium text-primary-text transition-colors duration-300 hover:bg-amber-700 ${sizeClasses[size]}`}
    >
      {children}
    </Link>
  );
}

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'Chalksmith.ai',
  description: 'AI-powered tool for creating educational content.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} bg-primary-bg text-primary-text antialiased`}>
        <ClerkProvider>
          <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
            <Link href="/" className="flex items-center gap-3" aria-label="Chalksmith.ai home">
              <span className="grid size-10 place-items-center rounded-lg border border-stone-700 bg-stone-50 text-stone-950">
                <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
              </span>
              <span className="hidden text-md font-semibold text-stone-50 sm:inline">Chalksmith.ai</span>
            </Link>
            <nav className="flex items-center gap-10 text-sm font-medium text-stone-300">
              <a className="transition-colors hover:text-stone-50" href="#content">
                Content
              </a>
              <a className="transition-colors hover:text-stone-50" href="#about">
                About us
              </a>
            </nav>
            <Show when="signed-out">
              <SignUpButton mode="modal">
                <button className="flex items-center justify-center gap-2 rounded-lg bg-accent font-medium text-primary-text transition-colors duration-300 hover:bg-amber-700 ${sizeClasses[size]} px-4 py-2 text-sm">
                  Create Account
                  <LogIn className="size-4" />
                </button>
              </SignUpButton>
            </Show>
            <Show when="signed-in">
              <UserButton />
            </Show>
          </header>
          {children}
        </ClerkProvider>
      </body>
    </html>
  )
}