'use client';

import { ArrowDown, ArrowUp, ExternalLink, X } from 'lucide-react';
import Link from 'next/link';

import LessonFormatIcon from '@/components/dashboard/LessonFormatIcon';
import type { LessonSetLessonItem } from '@/lib/types/api';

interface LessonSetLessonRowProps {
  lesson: LessonSetLessonItem;
  index: number;
  total: number;
  isBusy: boolean;
  onMove: (direction: -1 | 1) => void;
  onRemove: () => void;
}

export default function LessonSetLessonRow({
  lesson,
  index,
  total,
  isBusy,
  onMove,
  onRemove,
}: LessonSetLessonRowProps) {
  return (
    <li className="flex items-center gap-4 rounded-xl border border-border bg-secondary-bg p-4 shadow-md shadow-stone-950/10">
      <span className="grid size-8 shrink-0 place-items-center rounded-full bg-primary-bg text-sm font-semibold text-secondary-text">
        {index + 1}
      </span>
      <LessonFormatIcon format={lesson.format} />
      <section className="min-w-0 flex-1">
        <h3 className="truncate font-semibold text-primary-text">{lesson.topic}</h3>
        <p className="mt-1 line-clamp-1 text-sm text-secondary-text">{lesson.summary || 'No description yet.'}</p>
      </section>
      <section className="flex shrink-0 items-center gap-1">
        <button
          type="button"
          disabled={isBusy || index === 0}
          onClick={() => onMove(-1)}
          className="rounded-lg p-2 text-secondary-text hover:bg-primary-text/10 hover:text-primary-text disabled:opacity-25"
          aria-label={`Move ${lesson.topic} up`}
        >
          <ArrowUp size={17} />
        </button>
        <button
          type="button"
          disabled={isBusy || index === total - 1}
          onClick={() => onMove(1)}
          className="rounded-lg p-2 text-secondary-text hover:bg-primary-text/10 hover:text-primary-text disabled:opacity-25"
          aria-label={`Move ${lesson.topic} down`}
        >
          <ArrowDown size={17} />
        </button>
        <Link
          href={`/generation?lessonId=${lesson.id}`}
          className="rounded-lg p-2 text-secondary-text hover:bg-primary-text/10 hover:text-accent"
          aria-label={`Open ${lesson.topic}`}
        >
          <ExternalLink size={17} />
        </Link>
        <button
          type="button"
          disabled={isBusy}
          onClick={onRemove}
          className="rounded-lg p-2 text-secondary-text hover:bg-red-950/40 hover:text-red-300 disabled:opacity-40"
          aria-label={`Remove ${lesson.topic} from set`}
        >
          <X size={18} />
        </button>
      </section>
    </li>
  );
}
