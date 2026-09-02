import LessonCardSkeleton from '@/components/lesson/LessonCardSkeleton';
import Skeleton, { ChalkLoader } from '@/components/ui/Skeleton';

export default function DashboardShellSkeleton() {
  return (
    <main
      aria-busy="true"
      className="app-route-without-site-header relative flex h-screen w-full overflow-hidden bg-primary-bg font-sans text-primary-text"
    >
      <aside className="hidden h-full w-1/5 min-w-64 flex-col border-r border-border bg-secondary-bg p-4 md:flex">
        <header className="flex h-10 items-center gap-3">
          <Skeleton className="size-9 rounded-xl" />
          <Skeleton className="h-5 w-28" />
        </header>
        <Skeleton className="mt-6 h-11 w-full rounded-lg" />
        <Skeleton className="mt-6 h-3 w-20" />
        <section className="mt-3 space-y-3">
          {Array.from({ length: 5 }, (_, index) => <Skeleton key={index} className="h-10 w-full rounded-lg" />)}
        </section>
        <Skeleton className="mt-auto size-10 rounded-full" />
      </aside>
      <section className="flex-1 overflow-hidden px-8 pb-8 pt-5">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <Skeleton className="h-9 w-44" />
          <ChalkLoader compact label="Loading your dashboard" />
        </header>
        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, index) => <LessonCardSkeleton key={index} />)}
        </section>
      </section>
    </main>
  );
}
