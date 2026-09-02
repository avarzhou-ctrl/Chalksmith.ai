interface SkeletonProps {
  className?: string;
}

interface ChalkLoaderProps {
  label?: string;
  compact?: boolean;
}

export default function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <span
      aria-hidden="true"
      className={`block rounded-md bg-stone-800/80 motion-safe:animate-pulse motion-reduce:animate-none ${className}`}
    />
  );
}

export function SkeletonStatus({ children }: { children: string }) {
  return <span className="sr-only" role="status">{children}</span>;
}

export function ChalkLoader({
  label = 'Preparing your chalkboard',
  compact = false,
}: ChalkLoaderProps) {
  return (
    <span
      role="status"
      aria-live="polite"
      className={`inline-flex items-center ${compact ? 'gap-3' : 'flex-col gap-4 text-center'}`}
    >
      <span
        aria-hidden="true"
        className={`relative shrink-0 ${compact ? 'size-8' : 'size-14'}`}
      >
        <span className="absolute inset-0 rounded-full border-2 border-stone-700" />
        <span className="absolute inset-0 rounded-full border-2 border-transparent border-r-amber-500 border-t-amber-500 motion-safe:animate-spin" />
        <span className="absolute inset-3 grid place-items-center rounded-full bg-stone-900 shadow-inner shadow-black/40">
          <span className="h-1 w-5 rotate-12 rounded-full bg-stone-100 motion-safe:animate-pulse" />
        </span>
      </span>
      <span className={compact ? 'text-sm text-secondary-text' : 'text-sm font-medium text-stone-200'}>
        {label}
      </span>
    </span>
  );
}
