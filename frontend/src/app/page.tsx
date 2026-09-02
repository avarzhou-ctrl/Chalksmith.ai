'use client';

import Link from 'next/link';
import { useState } from 'react';
import { SignUpButton, useAuth } from '@clerk/nextjs';
import { ArrowRight } from 'lucide-react';
import ChalkDust from '@/components/home/ChalkDust';
import ClickSpark from '@/components/home/ClickSpark';
import CodeDrivenDemo from '@/components/home/CodeDrivenDemo';
import EducatorEquation from '@/components/home/EducatorEquation';
import ExamplesCarousel from '@/components/home/ExamplesCarousel';
import FaqSection from '@/components/home/FaqSection';
import Footer from '@/components/home/Footer';
import ForgeFrame from '@/components/home/ForgeFrame';
import LessonPipeline from '@/components/home/LessonPipeline';
import RotatingFormats from '@/components/home/RotatingFormats';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';
import { generationHref } from '@/lib/navigation';

const ctaBaseClasses = 'flex items-center justify-center gap-2 rounded-lg bg-accent font-medium text-primary-text shadow-lg shadow-amber-950/30 transition-all duration-300 hover:-translate-y-0.5 hover:bg-amber-700 hover:shadow-amber-900/30 active:translate-y-0 motion-reduce:transform-none';
const ctaSizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

function PrimaryCtaLink({ href, children, size = 'md' }: { href: string; children: React.ReactNode; size?: 'sm' | 'md' | 'lg' }) {
  return (
    <ClickSpark>
      <Link
        href={href}
        className={`${ctaBaseClasses} ${ctaSizeClasses[size]}`}
      >
        {children}
      </Link>
    </ClickSpark>
  );
}

function BuildLessonCta() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return (
      <PrimaryCtaLink href={generationHref} size="lg">
        Try Chalksmith Free
        <ArrowRight size={18} />
      </PrimaryCtaLink>
    );
  }

  if (isLoaded && isSignedIn) {
    return (
      <PrimaryCtaLink href={generationHref} size="lg">
        Try Chalksmith Free
        <ArrowRight size={18} />
      </PrimaryCtaLink>
    );
  }

  return (
    <ClickSpark>
      <SignUpButton mode="modal" forceRedirectUrl={generationHref} signInForceRedirectUrl={generationHref}>
        <button type="button" className={`${ctaBaseClasses} ${ctaSizeClasses.lg}`}>
          Try Chalksmith Free
          <ArrowRight size={18} />
        </button>
      </SignUpButton>
    </ClickSpark>
  );
}

export default function Home() {
  const [previewVideoLoaded, setPreviewVideoLoaded] = useState(false);

  return (
    <main className="relative min-h-screen overflow-hidden bg-primary-bg text-primary-text">
      <ChalkDust />
      <div className="relative z-10">
        <section id="landing" className="relative isolate w-full overflow-hidden px-4 py-12 text-center sm:px-6 sm:py-16 lg:px-8">
          <div className="absolute inset-0 z-1 bg-[radial-gradient(ellipse_at_center,rgba(28,25,23,0.08)_0%,rgba(12,10,9,0.24)_58%,rgba(12,10,9,0.7)_100%)]" />
          <div className="absolute inset-x-0 bottom-0 z-1 h-32 bg-gradient-to-b from-transparent to-primary-bg" />
          <div className="relative z-10 mx-auto w-full max-w-6xl">
            <div className="mx-auto max-w-5xl">
              <h1 className="mx-auto max-w-4xl text-4xl font-bold leading-tight text-primary-text sm:text-5xl">
                Forge stunning <span className="bg-gradient-to-r from-amber-300 via-amber-500 to-amber-700 bg-clip-text text-transparent">code-driven STEM animations</span> in minutes.
              </h1>
              <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-secondary-text">
                Upload your syllabus or describe a lesson, select a teaching format, and generate editable, code-driven videos, interactives, and slides instead of one-off static files.
              </p>
              <RotatingFormats />
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <BuildLessonCta />
                <a
                  href="#examples"
                  className="rounded-lg border border-stone-700 bg-stone-950/50 px-6 py-3 text-base font-medium text-primary-text backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-accent hover:text-accent motion-reduce:transform-none"
                >
                  View examples
                </a>
              </div>
            </div>
            <LessonPipeline />
          </div>
        </section>

        <section className="relative mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8" id="content" aria-label="Chalksmith product preview">
          <ForgeFrame>
            <div className="relative aspect-video">
              {!previewVideoLoaded && <Skeleton className="absolute inset-0 size-full rounded-none" />}
              <video
                src="/demo-1.mp4"
                autoPlay
                loop
                muted
                playsInline
                onLoadedData={() => setPreviewVideoLoaded(true)}
                onError={() => setPreviewVideoLoaded(true)}
                className={`size-full object-contain transition-opacity duration-300 ${previewVideoLoaded ? 'opacity-100' : 'opacity-0'}`}
              />
              {!previewVideoLoaded && <SkeletonStatus>Loading product preview</SkeletonStatus>}
            </div>
          </ForgeFrame>
        </section>

        <section id="about" className="relative bg-stone-950/40">
          <div aria-hidden="true" className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(217,119,6,0.07),transparent_58%)]" />
          <div className="relative mx-auto w-full max-w-6xl px-4 py-12 text-center sm:px-6 sm:py-16 lg:px-8">
            <h2 className="text-4xl font-bold text-primary-text sm:text-5xl">The Educator&apos;s Dilemma</h2>
            <EducatorEquation />
            <p className="mx-auto mt-8 max-w-xl text-base leading-6 text-secondary-text">
              — Marci Goldberg, K-12 Market Advisors.
            </p>
          </div>
        </section>

        <section id="why_choose_chalksmith" className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-4xl font-bold text-primary-text sm:text-5xl">Why Chalksmith?</h2>
          </div>
          <div className="mt-10 grid gap-6">
            <article className="relative overflow-hidden rounded-2xl border border-stone-800 bg-secondary-bg p-6 shadow-2xl shadow-black/20 sm:p-8">
              <span aria-hidden="true" className="absolute inset-x-20 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/60 to-transparent" />
              <div className="mb-8">
                <h3 className="text-2xl font-semibold text-primary-text">Code-driven production.</h3>
                <p className="mt-4 text-base leading-7 text-secondary-text">
                  Unlike black-box lesson generators, Chalksmith lets you inspect and reuse the source behind every lesson.
                </p>
              </div>
              <div className="w-full">
                <CodeDrivenDemo
                  filePath="/demo-2.html"
                />
              </div>
            </article>

            <div className="grid gap-6 lg:grid-cols-2">
              <article className="group flex flex-col rounded-2xl border border-stone-800 bg-secondary-bg p-6 shadow-xl shadow-black/15 transition-colors duration-300 hover:border-amber-600/40 sm:p-8">
                <div className="mb-8">
                  <h3 className="text-2xl font-semibold text-primary-text">Source uploads.</h3>
                  <p className="mt-4 text-base leading-7 text-secondary-text">
                    Start from syllabus notes, readings, or lesson goals so every generated asset stays close to your curriculum.
                  </p>
                </div>
                <div className="w-full mt-auto">
                  <div className="w-full overflow-hidden rounded-2xl border border-border bg-primary-bg shadow-2xl transition-colors duration-300 group-hover:border-amber-700/40">
                    <video 
                      src="/demo-4.mp4"
                      autoPlay 
                      loop 
                      muted 
                      playsInline 
                      className="w-full h-full" 
                    />
                  </div>
                </div>
              </article>

              <article className="group flex flex-col rounded-2xl border border-stone-800 bg-secondary-bg p-6 shadow-xl shadow-black/15 transition-colors duration-300 hover:border-amber-600/40 sm:p-8">
                <div className="mb-8">
                  <h3 className="text-2xl font-semibold text-primary-text">Built-in transparency.</h3>
                  <p className="mt-4 text-base leading-7 text-secondary-text">
                    Make edits within seconds while reviewing the code and lesson structure that produced the final result.
                  </p>
                </div>
                <div className="w-full mt-auto">
                  <div className="w-full overflow-hidden rounded-2xl border border-border bg-primary-bg shadow-2xl transition-colors duration-300 group-hover:border-amber-700/40">
                    <video 
                      src="/demo-3.mp4"
                      autoPlay 
                      loop 
                      muted 
                      playsInline 
                      className="w-full h-full" 
                    />
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>
        
        <section id="examples" className="bg-stone-950/40">
          <div className="mx-auto w-full max-w-6xl px-4 py-12 text-center sm:px-6 sm:py-16 lg:px-8">
            <h2 className="text-4xl font-bold text-primary-text sm:text-5xl">Examples</h2>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-secondary-text">
              Flip through generated lesson formats: video, interactive display, and slides.
            </p>
            <Link
              href="/content/"
              className="mx-auto mt-5 inline-flex items-center gap-2 text-sm font-semibold text-amber-400 transition-colors hover:text-amber-300"
            >
              Explore all lessons
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
            <ExamplesCarousel />
          </div>
        </section>

        <FaqSection />

        <section id="call_to_action" className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
          <div className="relative overflow-hidden rounded-2xl border border-amber-700/30 bg-secondary-bg p-6 text-left shadow-2xl shadow-black/20 sm:p-10">
            <span aria-hidden="true" className="absolute -right-20 -top-24 size-64 rounded-full bg-amber-600/10 blur-3xl" />
            <span aria-hidden="true" className="absolute inset-x-20 top-0 h-px bg-gradient-to-r from-transparent via-amber-400/70 to-transparent" />
            <h2 className="relative mt-5 max-w-5xl text-4xl font-bold text-primary-text lg:whitespace-nowrap xl:text-5xl">
              Save 12 hours every week on lesson creation.
            </h2>
            <p className="relative mt-4 text-2xl font-semibold text-accent">Try Chalksmith.ai today.</p>
            <div className="relative mb-4 mt-7 inline-flex">
              <BuildLessonCta />
            </div>
          </div>
        </section>

        <Footer/>
      </div>
    </main>
  );
}
