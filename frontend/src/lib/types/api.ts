export type LessonFormat = 'interactive' | 'slides' | 'video';

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface Lesson {
  id: string;
  topic: string;
  format: LessonFormat;
  status: 'generating' | 'ready' | 'failed' | 'deleting';
  summary: string | null;
  source_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type LessonListItem = Pick<
  Lesson,
  'id' | 'topic' | 'format' | 'status' | 'summary' | 'created_at' | 'updated_at'
>;

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
  | { type: 'progress'; stage: GenerationStage; message: string }
  | { type: 'complete'; lesson_id: string }
  | { type: 'error'; code: string; message: string; lesson_id?: string };

export interface AccessUrl {
  url: string;
  expires_in: number;
}
