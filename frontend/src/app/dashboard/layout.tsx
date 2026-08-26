import type { ReactNode } from 'react';

import { LessonFoldersProvider } from '@/components/dashboard/LessonFoldersProvider';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <LessonFoldersProvider>{children}</LessonFoldersProvider>;
}
