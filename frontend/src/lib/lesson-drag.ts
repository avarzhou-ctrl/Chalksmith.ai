export const LESSON_DRAG_MIME = 'application/x-chalksmith-lesson';
export const LESSON_MOVED_EVENT = 'chalksmith:lesson-moved';
export const LESSON_ADDED_TO_SET_EVENT = 'chalksmith:lesson-added-to-set';
export const LESSON_SETS_CHANGED_EVENT = 'chalksmith:lesson-sets-changed';

const LESSON_TEXT_PREFIX = 'chalksmith-lesson:';

export interface LessonDragPayload {
  lessonId: string;
  title: string;
}

export interface LessonMovedDetail {
  lessonId: string;
  folderId: string | null;
}

export interface LessonAddedToSetDetail {
  lessonId: string;
  lessonSetId: string;
}

export function setLessonDragData(dataTransfer: DataTransfer, payload: LessonDragPayload) {
  const serialized = JSON.stringify(payload);
  dataTransfer.effectAllowed = 'copyMove';
  dataTransfer.setData(LESSON_DRAG_MIME, serialized);
  dataTransfer.setData('text/plain', `${LESSON_TEXT_PREFIX}${serialized}`);
}

export function getLessonDragData(dataTransfer: DataTransfer): LessonDragPayload | null {
  const customData = dataTransfer.getData(LESSON_DRAG_MIME);
  const textData = dataTransfer.getData('text/plain');
  const serialized = customData || (textData.startsWith(LESSON_TEXT_PREFIX)
    ? textData.slice(LESSON_TEXT_PREFIX.length)
    : '');

  if (!serialized) return null;
  try {
    const parsed = JSON.parse(serialized) as Partial<LessonDragPayload>;
    if (typeof parsed.lessonId !== 'string' || typeof parsed.title !== 'string') return null;
    return { lessonId: parsed.lessonId, title: parsed.title };
  } catch {
    return null;
  }
}

export function dispatchLessonMoved(detail: LessonMovedDetail) {
  window.dispatchEvent(new CustomEvent<LessonMovedDetail>(LESSON_MOVED_EVENT, { detail }));
}

export function dispatchLessonAddedToSet(detail: LessonAddedToSetDetail) {
  window.dispatchEvent(new CustomEvent<LessonAddedToSetDetail>(LESSON_ADDED_TO_SET_EVENT, { detail }));
}

export function dispatchLessonSetsChanged() {
  window.dispatchEvent(new Event(LESSON_SETS_CHANGED_EVENT));
}
