import { Flame } from 'lucide-react';

interface LoadingOverlayProps {
  progress: number;
  status: string | null;
}

export default function LoadingOverlay({ progress, status }: LoadingOverlayProps) {
  const isDeterminate = progress > 0;

  return (
    <section className="absolute inset-0 z-50 grid place-items-center bg-primary-bg/90 p-8 backdrop-blur-xl">
      <div className="w-full max-w-md text-center">
        <Flame className="mx-auto size-16 animate-pulse text-accent" />
        <h2 className="mt-6 text-3xl font-bold text-accent">Chalksmith.ai</h2>
        <p className="mt-2 text-sm text-secondary-text">{status ?? 'Loading lesson…'}</p>
        <div
          className="mt-8 h-1.5 overflow-hidden rounded-full bg-surface"
          role="progressbar"
          aria-label={status ?? 'Loading lesson'}
          aria-valuemin={isDeterminate ? 0 : undefined}
          aria-valuemax={isDeterminate ? 100 : undefined}
          aria-valuenow={isDeterminate ? progress : undefined}
          aria-valuetext={isDeterminate ? `${progress}%` : 'Loading'}
        >
          {isDeterminate ? (
            <div className="h-full bg-accent transition-all duration-500" style={{ width: `${progress}%` }} />
          ) : (
            <div className="h-full w-1/3 animate-progress-indeterminate rounded-full bg-accent motion-reduce:w-full motion-reduce:animate-none" />
          )}
        </div>
      </div>
    </section>
  );
}
