// src/app/layout.tsx
import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

import Link from 'next/link'
import { AuthButton } from '@/components/auth/AuthButton'
import { dashboardHref, homeHref } from '@/lib/navigation'

const configuredDomain = process.env.NEXT_PUBLIC_SITE_DOMAIN
const siteDomain = configuredDomain || 'chalksmith.ai'

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
        <ClerkProvider
          appearance={{
            variables: {
              colorPrimary: '#d97706',
              colorPrimaryForeground: '#fafaf9',
              colorBackground: '#1c1917',
              colorForeground: '#fafaf9',
              colorMuted: '#292524',
              colorMutedForeground: '#a8a29e',
              colorInput: '#0c0a09',
              colorInputForeground: '#fafaf9',
              colorBorder: '#44403c',
              colorRing: '#d97706',
              colorModalBackdrop: 'rgba(12, 10, 9, 0.8)',
              fontFamily: 'Inter, ui-sans-serif, system-ui, sans-serif',
              borderRadius: '0.5rem',
            },
            elements: {
              formButtonPrimary: '!text-stone-950',
              socialButtonsBlockButton: '!border-stone-700 !text-stone-50 hover:!bg-stone-700',
            },
          }}
        >
          <header
            data-site-header
            className="sticky top-0 z-50 mx-auto grid w-full max-w-7xl grid-cols-[1fr_auto_1fr] items-center gap-1 border-b border-stone-800 bg-primary-bg/90 px-4 py-5 backdrop-blur sm:px-6 lg:px-8"
          >
            <Link href={homeHref} className="flex items-center gap-3 justify-self-start" aria-label="Chalksmith.ai home">
              <span className="grid size-10 place-items-center rounded-lg text-stone-950">
                <img src="/logo.png" alt="Logo" className="h-8 w-8 object-contain" />
              </span>
              <span className="hidden text-base font-semibold text-stone-50 sm:inline">Chalksmith.ai</span>
            </Link>
            <nav className="flex min-w-0 items-center justify-center gap-3 text-base font-medium text-stone-300 max-[359px]:gap-2 max-[359px]:text-sm sm:gap-10 sm:text-base">
              <Link className="transition-colors hover:text-stone-50" href={dashboardHref}>
                Dashboard
              </Link>
              <Link className="transition-colors hover:text-stone-50" href="/content">
                Explore
              </Link>
              <Link className="transition-colors hover:text-stone-50" href="/about">
                About Us
              </Link>
            </nav>

            <span className="flex justify-self-end">
              <AuthButton />
            </span>
          </header>
          {children}
        </ClerkProvider>
      </body>
    </html>
  )
}
