import { RequireAuth } from '@/components/auth/RequireAuth';
import ProfileEditor from '@/components/profile/ProfileEditor';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';

function ProfilePageSkeleton() {
  return (
    <main className="min-h-screen bg-primary-bg px-6 py-16 font-sans text-primary-text">
      <section className="mx-auto max-w-2xl" aria-busy="true">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="mt-4 h-11 w-72" />
        <Skeleton className="mb-10 mt-5 h-5 w-full" />
        <section className="space-y-6">
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
          <Skeleton className="h-10 w-32 rounded-lg" />
        </section>
        <SkeletonStatus>Loading profile settings</SkeletonStatus>
      </section>
    </main>
  );
}

export default function ProfilePage() {
  return (
    <RequireAuth fallback={<ProfilePageSkeleton />}>
      <main className="min-h-screen bg-primary-bg px-6 py-16 font-sans text-primary-text">
        <section className="mx-auto max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Profile</p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight">Your public profile</h1>
          <p className="mb-10 mt-4 leading-7 text-secondary-text">
            Tell learners and teachers a little about the person behind your published lessons.
          </p>
          <ProfileEditor />
        </section>
      </main>
    </RequireAuth>
  );
}
