import { RequireAuth } from '@/components/auth/RequireAuth';
import ProfileEditor from '@/components/profile/ProfileEditor';

export default function ProfilePage() {
  return (
    <RequireAuth>
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
