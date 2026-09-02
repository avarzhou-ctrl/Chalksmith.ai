import { ClerkLoaded, ClerkLoading, SignUp } from '@clerk/nextjs';

import { ChalkLoader } from '@/components/ui/Skeleton';

export default function SignUpPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-primary-bg px-6 py-12">
      <ClerkLoading>
        <ChalkLoader label="Loading sign up" />
      </ClerkLoading>
      <ClerkLoaded>
        <SignUp />
      </ClerkLoaded>
    </main>
  );
}
