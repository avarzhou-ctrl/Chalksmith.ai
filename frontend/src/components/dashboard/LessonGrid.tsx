'use client';

import Link from 'next/link';
import { CirclePlus } from 'lucide-react';

import LessonCard from '@/components/dashboard/LessonCard';
import FormatOutput from '@/components/ui/FormatOutput';
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
    <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
      {showCreateCard && (
        <Link
          href="/generation"
          className="flex min-h-48 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-surface/30 p-6 text-center transition-colors hover:border-accent hover:bg-surface/40"
        >
          <CirclePlus className="text-accent" size={55} />
          <p className="mt-4 text-lg">Create New Lesson</p>
        </Link>
      )}

      {isLoading && (
        <p className="min-h-48 rounded-lg border border-border bg-surface/30 p-4 text-sm text-secondary-text">
          Loading lessons…
        </p>
      )}

      {!isLoading && lessons.length === 0 && !showCreateCard && (
        <section className="rounded-lg border border-border bg-surface/30 p-8 text-center md:col-span-2 lg:col-span-3">
          <h3 className="text-lg font-semibold text-primary-text">No lessons found</h3>
          <p className="mt-2 text-sm text-secondary-text">Try a different search term or format.</p>
        </section>
      )}

      {!isLoading && lessons.map((lesson) => (
        <LessonCard
          key={lesson.id}
          id={lesson.id}
          title={lesson.topic}
          description={lesson.summary ? <FormatOutput rawContent={lesson.summary} /> : null}
          format={lesson.format}
          status={lesson.status}
          isPublished={lesson.is_published}
          createdAt={lesson.created_at}
          versionCount={lesson.version_count}
          folderId={lesson.folder_id}
          folders={folders}
          onDelete={() => onDelete(lesson.id)}
          onMove={(folderId) => onMove(lesson.id, folderId)}
        />
      ))}
    </section>
  );
}
