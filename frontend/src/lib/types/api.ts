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
  folder_id: string | null;
  version_number: number;
  topic: string;
  format: LessonFormat;
  status: 'generating' | 'ready' | 'failed' | 'deleting';
  summary: string | null;
  source_code: string | null;
  spec_version: string | null;
  runtime_version: string | null;
  compiler_version: string | null;
  error_message: string | null;
  is_published: boolean;
  published_at: string | null;
  tags: string[];
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
  error_message: string | null;
  edit_instruction: string | null;
  is_final: boolean;
}

export type LessonListItem = Pick<
  Lesson,
  'id' | 'root_lesson_id' | 'folder_id' | 'topic' | 'format' | 'status' | 'summary' | 'is_published' | 'tags' | 'created_at' | 'updated_at'
> & { version_count: number; lesson_set_count: number };

export interface LessonListPage {
  items: LessonListItem[];
  next_cursor: string | null;
}

export interface LessonFolder {
  id: string;
  parent_id: string | null;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface LessonSetLessonItem {
  id: string;
  root_lesson_id: string;
  topic: string;
  format: LessonFormat;
  status: Lesson['status'];
  summary: string | null;
  position: number;
}

export interface LessonSetListItem {
  id: string;
  title: string;
  description: string;
  lesson_count: number;
  preview_lessons: LessonSetLessonItem[];
  created_at: string;
  updated_at: string;
}

export interface LessonSetDetail {
  id: string;
  title: string;
  description: string;
  lessons: LessonSetLessonItem[];
  created_at: string;
  updated_at: string;
}

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

export interface FinalLessonSelection {
  root_lesson_id: string;
  final_lesson_id: string;
}

export interface LessonPublication {
  root_lesson_id: string;
  lesson_id: string;
  is_published: boolean;
  published_at: string | null;
}

export interface LessonTags {
  root_lesson_id: string;
  tags: string[];
}

export interface PublishedLessonItem {
  id: string;
  root_lesson_id: string;
  topic: string;
  format: LessonFormat;
  summary: string | null;
  published_at: string;
  updated_at: string;
  author_profile_id: string;
  author_display_name: string;
  like_count: number;
  tags: string[];
}

export interface PublishedLessonLikeResponse {
  root_lesson_id: string;
  liked: boolean;
  like_count: number;
}

export interface PublishedTagItem {
  label: string;
  value: string;
  lesson_count: number;
}

export type LessonTagItem = PublishedTagItem;

export interface PublicProfile {
  id: string;
  display_name: string;
  bio: string;
  updated_at: string;
}
