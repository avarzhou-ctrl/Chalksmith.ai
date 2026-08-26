import PublicProfileView from '@/components/profile/PublicProfileView';

export default async function PublicProfilePage({
  params,
}: {
  params: Promise<{ profileId: string }>;
}) {
  const { profileId } = await params;
  return (
    <main className="min-h-screen bg-primary-bg px-6 py-16 font-sans text-primary-text">
      <section className="mx-auto max-w-2xl">
        <PublicProfileView profileId={profileId} />
      </section>
    </main>
  );
}
