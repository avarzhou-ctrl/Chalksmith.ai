import Skeleton from '@/components/ui/Skeleton';

export default function LessonSetCardSkeleton() {
  return (
    <article aria-hidden="true" className="flex min-h-64 flex-col rounded-2xl border border-border bg-secondary-bg p-5 shadow-lg shadow-stone-950/20">
      <header className="flex items-start gap-3">
        <Skeleton className="size-11 shrink-0 rounded-xl" />
        <section className="min-w-0 flex-1">
          <Skeleton className="h-6 w-4/5" />
          <Skeleton className="mt-2 h-4 w-2/5" />
        </section>
      </header>
      <Skeleton className="mt-5 h-4 w-full" />
      <Skeleton className="mt-2 h-4 w-3/4" />
      <section className="mt-5 space-y-2">
        <Skeleton className="h-9 w-full rounded-lg" />
        <Skeleton className="h-9 w-full rounded-lg" />
      </section>
      <footer className="mt-auto pt-6">
        <Skeleton className="h-4 w-20" />
      </footer>
    </article>
  );
}
