import { ClerkLoaded, ClerkLoading, SignIn } from '@clerk/nextjs';

import { ChalkLoader } from '@/components/ui/Skeleton';

export default function SignInPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-primary-bg px-6 py-12">
      <ClerkLoading>
        <ChalkLoader label="Loading sign in" />
      </ClerkLoading>
      <ClerkLoaded>
        <SignIn />
      </ClerkLoaded>
    </main>
  );
}
