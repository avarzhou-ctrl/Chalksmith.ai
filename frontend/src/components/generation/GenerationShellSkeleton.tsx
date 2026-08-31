import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';

export default function GenerationShellSkeleton() {
  return (
    <main className="app-route-without-site-header flex h-screen w-full overflow-hidden bg-primary-bg font-sans text-primary-text">
      <section className="flex w-3/4 flex-col p-5">
        <header className="flex items-center gap-4">
          <Skeleton className="size-10 rounded-xl" />
          <Skeleton className="h-8 w-56" />
          <Skeleton className="ml-auto h-9 w-28 rounded-lg" />
        </header>
        <Skeleton className="mt-5 min-h-0 flex-1 rounded-3xl border border-border" />
      </section>
      <aside className="flex w-1/4 flex-col border-l border-border bg-secondary-bg p-5">
        <Skeleton className="h-7 w-32" />
        <section className="mt-8 space-y-4">
          <Skeleton className="h-20 w-5/6 rounded-2xl" />
          <Skeleton className="ml-auto h-16 w-4/5 rounded-2xl" />
          <Skeleton className="h-24 w-5/6 rounded-2xl" />
        </section>
        <Skeleton className="mt-auto h-28 w-full rounded-2xl" />
      </aside>
      <SkeletonStatus>Loading the lesson workspace</SkeletonStatus>
    </main>
  );
}
