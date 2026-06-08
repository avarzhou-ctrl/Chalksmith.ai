import Link from 'next/link';
import { ArrowRight, Braces, FileCode2, Layers3, Upload, LogIn } from 'lucide-react';
import FireParticleBackground from '@/components/home/FireParticleBackground';

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

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-primary-bg text-primary-text">
      <FireParticleBackground />
      <div className="relative z-10">
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
          <PrimaryCtaLink href="/generation" size="md">
            Login
            <LogIn size={18} />
          </PrimaryCtaLink>
        </header>

        <section className="mx-auto grid min-h-[32rem] w-full max-w-5xl place-items-center px-4 pb-6 pt-10 text-center sm:min-h-[36rem] sm:px-6 lg:px-8">
          <div>
            <h1 className="mx-auto max-w-4xl text-4xl font-bold leading-tight text-stone-50 sm:text-5xl lg:text-6xl">
              Forge stunning STEM animations in minutes.
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-stone-300">
              Upload your syllabus or describe a lesson, select a teaching format, and let AI build visual
              animations grounded in your curriculum.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <PrimaryCtaLink href="/generation" size="lg">
                Build a lesson now
                <ArrowRight size={18} />
              </PrimaryCtaLink>
              <a
                href="#content"
                className="rounded-lg border border-stone-700 px-6 py-3 text-base font-medium text-stone-200 transition-colors hover:border-accent hover:text-amber-300"
              >
                View examples
              </a>
            </div>
          </div>
        </section>

        <p className="mx-auto w-full max-w-6xl px-4 py-16 text-center text-sm leading-6 text-stone-300 sm:px-6 lg:px-8" id="content">
          screen recording
        </p>

        <section id="about" className="mx-auto w-full max-w-6xl px-4 py-16 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-stone-50 sm:text-5xl">The Educator&apos;s Dilemma</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-[1fr_auto_1fr_auto_1fr] md:items-center">
            {[
              ['5 hours', 'per week collecting resources.'],
              ['7 hours', 'per week building from scratch.'],
              ['12 hours', 'per week lost managing lessons.'],
            ].map(([value, label], index) => (
              <div key={value} className="contents">
                <div className="rounded-lg border border-stone-800 bg-secondary-bg p-6">
                  <p className="text-4xl font-bold text-accent">{value}</p>
                  <p className="mx-auto mt-3 max-w-48 text-base leading-6 text-stone-200">{label}</p>
                </div>
                {index < 2 && <p className="hidden text-4xl font-bold text-stone-50 md:block">{index === 0 ? '+' : '='}</p>}
              </div>
            ))}
          </div>
          <p className="mx-auto mt-8 max-w-xl text-md leading-6 text-stone-300">
            — Marci Goldberg, K-12 Market Advisors.
          </p>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-stone-50 sm:text-5xl">Why choose Chalksmith?</h2>
          <div className="mt-8 grid gap-6">
            <article className="grid gap-6 rounded-lg border border-stone-800 bg-secondary-bg p-5 md:grid-cols-[0.8fr_1.2fr]">
              <div>
                <div className="mb-4 flex size-11 items-center justify-center rounded-lg bg-accent/20 text-accent">
                  <Layers3 size={22} />
                </div>
                <h3 className="text-2xl font-semibold text-stone-50">Built-in transparency.</h3>
                <p className="mt-3 text-sm leading-6 text-stone-300">
                  Make edits within seconds while reviewing the code and lesson structure that produced the final result.
                </p>
              </div>
              <div className="min-h-56 border border-stone-700 bg-stone-200 p-4 text-stone-900">
                <div className="grid h-full place-items-center text-center text-sm font-semibold">
                  <span>Fast edit preview</span>
                </div>
              </div>
            </article>

            <div className="grid gap-6 lg:grid-cols-2">
              <article className="grid gap-6 rounded-lg border border-stone-800 bg-secondary-bg p-5 md:grid-cols-[0.8fr_1.2fr]">
                <div>
                  <div className="mb-4 flex size-11 items-center justify-center rounded-lg bg-accent/20 text-accent">
                    <Upload size={22} />
                  </div>
                  <h3 className="text-2xl font-semibold text-stone-50">Source uploads.</h3>
                  <p className="mt-3 text-sm leading-6 text-stone-300">
                    Start from syllabus notes, readings, or lesson goals so every generated asset stays close to your curriculum.
                  </p>
                </div>
                <div className="min-h-56 border border-stone-700 bg-stone-200 p-4 text-stone-900">
                  <div className="grid h-full place-items-center text-center text-sm font-semibold">
                    <span>Syllabus upload preview</span>
                  </div>
                </div>
              </article>

              <article className="grid gap-6 rounded-lg border border-stone-800 bg-secondary-bg p-5 md:grid-cols-[0.8fr_1.2fr]">
                <div>
                  <div className="mb-4 flex size-11 items-center justify-center rounded-lg bg-accent/20 text-accent">
                    <FileCode2 size={22} />
                  </div>
                  <h3 className="text-2xl font-semibold text-stone-50">Code-driven production.</h3>
                  <p className="mt-3 text-sm leading-6 text-stone-300">
                    Generate reusable videos, interactives, and slides from source code instead of one-off static files.
                  </p>
                </div>
                <div className="min-h-56 border border-stone-700 bg-stone-200 p-4 text-stone-900">
                  <div className="h-full bg-stone-950 p-4 font-mono text-xs text-stone-200">
                    <div className="mb-3 flex items-center gap-2 text-accent">
                      <Braces size={16} />
                      render_lesson.tsx
                    </div>
                    <p>const scene = buildStemScene(&quot;water cycle&quot;);</p>
                    <p className="text-stone-500">scene.addCaption(&quot;Evaporation begins here&quot;);</p>
                    <p className="text-accent">export default scene;</p>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>
        
        <section className="mx-auto w-full max-w-6xl px-4 py-16 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-stone-50 sm:text-5xl">Examples</h2>
          
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 pb-40 pt-8 sm:px-6 lg:px-8">
          <div className="text-left">
            <h2 className="mt-5 text-3xl font-bold text-stone-50 sm:text-5xl">
              Stop spending 12 hours a week on slide decks.
            </h2>
            <p className="mt-4 text-2xl font-semibold text-accent">Try Chalksmith.ai today.</p>
            <div className="mt-7 inline-flex">
              <PrimaryCtaLink href="/generation" size="lg">
                Build a lesson now
                <ArrowRight size={18} />
              </PrimaryCtaLink>
            </div>
          </div>
        </section>

        <footer className="border-t border-stone-800 bg-primary-bg/90">
          <div className="mx-auto grid w-full max-w-7xl gap-8 px-4 py-10 text-sm text-stone-400 sm:px-6 md:grid-cols-[1fr_auto] lg:px-8">
            <div>
              <div className="flex items-center gap-3 text-stone-50">
                <span className="grid size-9 place-items-center rounded-lg bg-stone-50 text-stone-950">
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
                  <li><a className="hover:text-accent" href="/privacy">Privacy Policy</a></li>
                  <li><a className="hover:text-accent" href="/terms">Terms of Use</a></li>
                  <li><a className="hover:text-accent" href="/student-privacy">Student Privacy</a></li>
                  <li><a className="hover:text-accent" href="/accessibility">Accessibility</a></li>
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
