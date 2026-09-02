'use client';

import Link from 'next/link';
import { CirclePlus } from 'lucide-react';

import LessonCard from '@/components/dashboard/LessonCard';
import LessonCardSkeleton from '@/components/lesson/LessonCardSkeleton';
import FormatOutput from '@/components/ui/FormatOutput';
import { ChalkLoader } from '@/components/ui/Skeleton';
import type { LessonFolder, LessonListItem } from '@/lib/types/api';

interface LessonGridProps {
  lessons: LessonListItem[];
  isLoading: boolean;
  onDelete: (lessonId: string) => void;
  onMove: (lessonId: string, folderId: string | null) => Promise<void>;
  folders: LessonFolder[];
  showCreateCard?: boolean;
}

export default function LessonGrid({
  lessons,
  isLoading,
  onDelete,
  onMove,
  folders,
  showCreateCard = false,
}: LessonGridProps) {
  return (
    <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3" aria-busy={isLoading}>
      {showCreateCard && (
        <Link
          href="/generation"
          prefetch={false}
          className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-secondary-bg p-5 text-center shadow-lg shadow-stone-950/20 transition-colors hover:border-accent hover:bg-surface/30"
        >
          <CirclePlus className="text-accent" size={55} />
          <p className="mt-4 text-lg">Create New Lesson</p>
        </Link>
      )}

      {isLoading && lessons.length === 0 && Array.from(
        { length: showCreateCard ? 2 : 3 },
        (_, index) => <LessonCardSkeleton key={index} />,
      )}
      {isLoading && (
        <span className="col-span-full flex justify-center py-2">
          <ChalkLoader compact label="Loading lessons" />
        </span>
      )}

      {!isLoading && lessons.length === 0 && !showCreateCard && (
        <section className="rounded-2xl border border-border bg-secondary-bg p-8 text-center md:col-span-2 lg:col-span-3">
          <h3 className="text-lg font-semibold text-primary-text">No lessons found</h3>
          <p className="mt-2 text-sm text-secondary-text">Try a different search term or format.</p>
        </section>
      )}

      {lessons.map((lesson) => (
        <LessonCard
          key={lesson.id}
          id={lesson.id}
          title={lesson.topic}
          description={lesson.summary ? <FormatOutput rawContent={lesson.summary} /> : null}
          format={lesson.format}
          status={lesson.status}
          isPublished={lesson.is_published}
          tags={lesson.tags}
          createdAt={lesson.created_at}
          versionCount={lesson.version_count}
          lessonSetCount={lesson.lesson_set_count}
          folderId={lesson.folder_id}
          folders={folders}
          onDelete={() => onDelete(lesson.id)}
          onMove={(folderId) => onMove(lesson.id, folderId)}
        />
      ))}
    </section>
  );
}
