'use client';

import Link from 'next/link';
import { SignUpButton, useUser } from '@clerk/nextjs';
import { ArrowRight } from 'lucide-react';
import CodeDrivenDemo from '@/components/home/CodeDrivenDemo';

const ctaBaseClasses = 'flex items-center justify-center gap-2 rounded-lg bg-accent font-medium text-primary-text transition-colors duration-300 hover:bg-amber-700';
const ctaSizeClasses = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

function PrimaryCtaLink({ href, children, size = 'md' }: { href: string; children: React.ReactNode; size?: 'sm' | 'md' | 'lg' }) {
  return (
    <Link
      href={href}
      className={`${ctaBaseClasses} ${ctaSizeClasses[size]}`}
    >
      {children}
    </Link>
  );
}

function BuildLessonCta() {
  const { isLoaded, isSignedIn } = useUser();

  if (isLoaded && isSignedIn) {
    return (
      <PrimaryCtaLink href="https://app.chalksmith.ai" size="lg">
        Build a lesson now
        <ArrowRight size={18} />
      </PrimaryCtaLink>
    );
  }

  return (
    <SignUpButton mode="modal">
      <button type="button" className={`${ctaBaseClasses} ${ctaSizeClasses.lg}`}>
        Build a lesson now
        <ArrowRight size={18} />
      </button>
    </SignUpButton>
  );
}

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-primary-bg text-primary-text">
      <div className="relative z-10">
        <section id="landing" className="relative isolate grid min-h-[32rem] w-full overflow-hidden bg-primary-bg px-4 pb-6 pt-10 text-center sm:min-h-[36rem] sm:px-6 lg:px-8">
          <div className="absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_center,rgba(0,0,0,0.72)_0%,rgba(0,0,0,0.52)_32%,rgba(0,0,0,0.14)_66%,rgba(0,0,0,0.84)_100%)]" />
          <div className="relative z-10 mx-auto grid w-full max-w-5xl place-items-center">
            <div>
              <h1 className="mx-auto max-w-4xl text-4xl font-bold leading-tight text-primary-text sm:text-5xl lg:text-6xl">
                Forge stunning STEM animations in minutes.
              </h1>
              <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-secondary-text">
                Upload your syllabus or describe a lesson, select a teaching format, and let AI build visual
                animations grounded in your curriculum.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <BuildLessonCta />
                <a
                  href="#examples"
                  className="rounded-lg border border-secondary-bg px-6 py-3 text-base font-medium text-primary-text transition-colors hover:border-accent hover:text-accent"
                >
                  View examples
                </a>
              </div>
            </div>
          </div>
        </section>

        <div className="mx-auto w-full max-w-6xl px-4 py-16 text-center text-sm leading-6 text-secondary-text sm:px-6 lg:px-8" id="content">
          <video 
            src="/demo_1.mp4" 
            autoPlay 
            loop 
            muted 
            playsInline 
            className="mx-auto rounded-lg border border-secondary-bg shadow-lg shadow-accent/20" 
          />
        </div>

        <section id="about" className="mx-auto w-full max-w-6xl px-4 py-16 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-primary-text sm:text-5xl">The Educator&apos;s Dilemma</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-center">
            {[
              ['5 hours', 'per week collecting resources.'],
              ['7 hours', 'per week building from scratch.'],
              ['12 hours', 'per week lost managing lessons.'],
            ].map(([value, label], index) => (
              <div key={value} className="contents">
                <div className="rounded-lg border border-secondary-bg bg-secondary-bg p-6">
                  <p className="text-4xl font-bold text-accent">{value}</p>
                  <p className="mx-auto mt-3 max-w-48 text-base leading-6 text-primary-text">{label}</p>
                </div>
                {index < 2 && <p className="hidden text-4xl font-bold text-stone-50 md:block">{index === 0 ? '+' : '='}</p>}
              </div>
            ))}
          </div>
          <p className="mx-auto mt-8 max-w-xl text-md leading-6 text-secondary-text">
            — Marci Goldberg, K-12 Market Advisors.
          </p>
        </section>

        <section id="why_choose_chalksmith" className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-primary-text sm:text-5xl">Why choose Chalksmith?</h2>
          <div className="mt-8 grid gap-6">
            <article className="rounded-lg border border-secondary-bg bg-secondary-bg p-8">
              <div className="max-w-2xl mb-8">
                <h3 className="text-3xl font-semibold text-primary-text">Code-driven production.</h3>
                <p className="mt-4 text-lg leading-7 text-secondary-text">
                  Generate reusable videos, interactives, and slides from source code instead of one-off static files.
                </p>
              </div>
              <div className="w-full">
                <CodeDrivenDemo
                  filePath="/demo_2.html"
                />
              </div>
            </article>

            <div className="grid gap-6 lg:grid-cols-2">
              <article className="rounded-lg border border-secondary-bg bg-secondary-bg p-8 flex flex-col">
                <div className="mb-8">
                  <h3 className="text-2xl font-semibold text-primary-text">Source uploads.</h3>
                  <p className="mt-3 text-sm leading-6 text-secondary-text">
                    Start from syllabus notes, readings, or lesson goals so every generated asset stays close to your curriculum.
                  </p>
                </div>
                <div className="mt-auto min-h-56 rounded-lg border border-secondary-bg bg-primary-text p-4 text-secondary-bg">
                  <div className="grid h-full place-items-center text-center text-sm font-semibold">
                    <span>Coming soon!</span>
                  </div>
                </div>
              </article>

              <article className="rounded-lg border border-secondary-bg bg-secondary-bg p-8 flex flex-col">
                <div className="mb-8">
                  <h3 className="text-2xl font-semibold text-primary-text">Built-in transparency.</h3>
                  <p className="mt-3 text-sm leading-6 text-secondary-text">
                    Make edits within seconds while reviewing the code and lesson structure that produced the final result.
                  </p>
                </div>
                <div className="mt-auto min-h-56 rounded-lg border border-secondary-bg bg-primary-text p-4 text-secondary-bg">
                  <div className="grid h-full place-items-center text-center text-sm font-semibold">
                    <span>Fast edit preview</span>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>
        
        <section id="examples" className="mx-auto w-full max-w-6xl px-4 py-16 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-primary-text sm:text-5xl">Examples</h2>
          
        </section>

        <section id="call_to_action" className="mx-auto w-full max-w-6xl px-4 pb-40 pt-8 sm:px-6 lg:px-8">
          <div className="text-left rounded-lg border border-secondary-bg bg-secondary-bg p-5 md:grid-cols-[0.8fr_1.2fr]">
            <h2 className="mt-5 text-3xl font-bold text-primary-text sm:text-5xl">
              Stop spending 12 hours a week on slide decks.
            </h2>
            <p className="mt-4 text-2xl font-semibold text-accent">Try Chalksmith.ai today.</p>
            <div className="mt-7 mb-4 inline-flex">
              <BuildLessonCta />
            </div>
          </div>
        </section>

        <footer className="border-t border-secondary-bg bg-primary-bg/90">
          <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-10 text-sm text-secondary-text sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
            <div>
              <div className="flex items-center gap-3 text-primary-text">
                <span className="grid size-9 place-items-center rounded-lg text-primary-bg">
                  <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain" />
                </span>
                <span className="font-semibold">Chalksmith.ai</span>
              </div>
              <p className="mt-4 max-w-md leading-6">
                Classroom-focused AI tools for creating, reviewing, and presenting STEM teaching materials.
              </p>
              <p className="mt-4">Copyright © 2026 Chalksmith.ai. All rights reserved.</p>
            </div>
            <div className="grid gap-8 sm:grid-cols-2 sm:gap-12 md:justify-self-end">
              <div>
                <h3 className="font-semibold text-stone-50">Legal</h3>
                <ul className="mt-4 space-y-3">
                  <li><a className="hover:text-accent" href="/privacy-policy">Privacy Policy</a></li>
                  <li><a className="hover:text-accent" href="/terms-of-service">Terms of Service</a></li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-stone-50">Contact</h3>
                <ul className="mt-4 space-y-3">
                  <li><a className="hover:text-accent" href="mailto:help@chalksmith.ai">help@chalksmith.ai</a></li>
                </ul>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
