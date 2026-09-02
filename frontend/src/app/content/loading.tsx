import LessonCardSkeleton from '@/components/lesson/LessonCardSkeleton';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';

export default function ContentLoading() {
  return (
    <main
      aria-busy="true"
      className="min-h-screen bg-primary-bg px-6 py-16 font-sans text-primary-text sm:px-10 lg:px-16"
    >
      <section className="mx-auto w-full max-w-7xl">
        <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <section className="w-full max-w-3xl">
            <Skeleton className="h-12 w-64" />
            <section className="mt-4 space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-4/5" />
            </section>
          </section>
          <Skeleton className="h-10 w-40 rounded-xl" />
        </header>

        <section className="my-8 flex flex-col gap-3">
          <section className="flex flex-col gap-3 lg:flex-row">
            <Skeleton className="h-12 flex-1 rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl lg:w-64" />
          </section>
          <section className="flex gap-2">
            <Skeleton className="h-7 w-20 rounded-full" />
            <Skeleton className="h-7 w-24 rounded-full" />
            <Skeleton className="h-7 w-16 rounded-full" />
          </section>
        </section>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }, (_, index) => <LessonCardSkeleton key={index} />)}
        </section>
        <SkeletonStatus>Loading published lessons</SkeletonStatus>
      </section>
    </main>
  );
}
