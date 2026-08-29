import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import type { PublishedLessonItem } from '@/lib/types/api';

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lessonId: string }>;
}): Promise<Metadata> {
  const { lessonId } = await params;
  try {
    const response = await fetch(`${apiBaseUrl}/v2/explore/lessons/${lessonId}`, {
      cache: 'no-store',
    });
    if (!response.ok) throw new Error('Lesson metadata unavailable.');
    const lesson = await response.json() as PublishedLessonItem;
    const description = lesson.summary || `A published Chalksmith lesson by ${lesson.author_display_name}.`;
    return {
      title: `${lesson.topic} | Chalksmith`,
      description,
      openGraph: {
        title: lesson.topic,
        description,
        images: [],
      },
      twitter: {
        card: 'summary',
        title: lesson.topic,
        description,
        images: [],
      },
    };
  } catch {
    return {
      title: 'Published lesson | Chalksmith',
      description: 'View a lesson shared by the Chalksmith community.',
      openGraph: { images: [] },
      twitter: { images: [] },
    };
  }
}

export default function PublishedLessonLayout({ children }: { children: ReactNode }) {
  return children;
}
