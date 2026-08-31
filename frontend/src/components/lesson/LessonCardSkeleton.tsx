import Skeleton from '@/components/ui/Skeleton';

export default function LessonCardSkeleton() {
  return (
    <article aria-hidden="true" className="flex min-h-64 flex-col rounded-2xl border border-border bg-secondary-bg p-5 shadow-lg shadow-stone-950/20">
      <header className="flex items-start gap-3">
        <Skeleton className="size-11 shrink-0 rounded-xl" />
        <section className="min-w-0 flex-1">
          <Skeleton className="h-6 w-4/5" />
          <Skeleton className="mt-2 h-4 w-2/5" />
        </section>
        <Skeleton className="size-7 shrink-0" />
      </header>
      <section className="mt-5 space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-11/12" />
        <Skeleton className="h-4 w-3/5" />
      </section>
      <section className="mt-5 flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </section>
      <footer className="mt-auto flex items-center justify-between pt-6">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-20" />
      </footer>
    </article>
  );
}
