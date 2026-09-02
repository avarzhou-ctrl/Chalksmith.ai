import { ChalkLoader } from '@/components/ui/Skeleton';

export default function PublishedLessonLoading() {
  return (
    <main className="app-route-without-site-header grid h-screen place-items-center bg-primary-bg font-sans text-primary-text">
      <ChalkLoader label="Loading published lesson" />
    </main>
  );
}
