export const LESSON_FORMAT_OPTIONS = [
  { label: 'Interactive Display', value: 'interactive' },
  { label: 'Presentation', value: 'slides' },
  { label: 'Video', value: 'video' },
] as const;

export type LessonFormat = (typeof LESSON_FORMAT_OPTIONS)[number]['value'];

export function getLessonFormatLabel(format: LessonFormat): string {
  return LESSON_FORMAT_OPTIONS.find((option) => option.value === format)?.label ?? format;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface Lesson {
  id: string;
  root_lesson_id: string;
  parent_lesson_id: string | null;
  version_number: number;
  topic: string;
  format: LessonFormat;
  status: 'generating' | 'ready' | 'failed' | 'deleting';
  summary: string | null;
  source_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface LessonVersion {
  id: string;
  parent_lesson_id: string | null;
  version_number: number;
  topic: string;
  status: Lesson['status'];
  summary: string | null;
  edit_instruction: string | null;
}

export type LessonListItem = Pick<
  Lesson,
  'id' | 'root_lesson_id' | 'topic' | 'format' | 'status' | 'summary' | 'created_at' | 'updated_at'
> & { version_count: number };

export interface GenerationRequest {
  topic: string;
  format: LessonFormat;
  baseLessonId?: string;
  editInstruction?: string;
  sourceFiles?: File[];
}

export type GenerationStage =
  | 'validating'
  | 'generating'
  | 'rendering'
  | 'repairing'
  | 'saving'
  | 'complete'
  | 'error';

export type GenerationEvent =
  | { type: 'started'; lesson_id: string }
  | { type: 'progress'; stage: GenerationStage; message: string; generated_characters?: number }
  | { type: 'complete'; lesson_id: string }
  | { type: 'error'; code: string; message: string; lesson_id?: string };

export interface AccessUrl {
  url: string;
  expires_in: number;
}
