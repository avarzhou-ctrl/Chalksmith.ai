import {
  MousePointerClick,
  Presentation,
  Video,
  type LucideIcon,
} from 'lucide-react';

import { getLessonFormatLabel, type LessonFormat } from '@/lib/types/api';

const FORMAT_ICONS: Record<LessonFormat, LucideIcon> = {
  interactive: MousePointerClick,
  slides: Presentation,
  video: Video,
};

interface LessonFormatIconProps {
  format: LessonFormat;
}

export default function LessonFormatIcon({ format }: LessonFormatIconProps) {
  const Icon = FORMAT_ICONS[format];
  const label = getLessonFormatLabel(format);

  return (
    <span
      className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-accent/10 text-accent"
      aria-label={`${label} lesson`}
    >
      <Icon className="size-4" aria-hidden />
    </span>
  );
}
