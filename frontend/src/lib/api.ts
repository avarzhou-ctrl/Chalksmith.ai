export interface LessonRequest {
  topic: string;
  model: string;
  format: string;
}

export interface LessonResponse {
  id?: string;
  url: string;
  code: string;
}

export async function createLesson(request: LessonRequest): Promise<LessonResponse> {
    const response = await fetch('/api/lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create lesson');
    }

    return response.json();
}

export async function getLesson(topic: string, model: string, format: string): Promise<LessonResponse> {
    const params = new URLSearchParams({ topic, model, format });
    const response = await fetch(`/api/lesson?${params.toString()}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get lesson');
    }

    return response.json();
}
