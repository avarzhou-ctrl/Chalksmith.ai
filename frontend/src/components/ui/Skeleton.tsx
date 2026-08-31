interface SkeletonProps {
  className?: string;
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
