// Shared interfaces between frontend and backend to ensure type safety across the stack
export interface LessonRequest {
  topic: string;
  model: string;
  format: string;
  lesson_id?: string;
  prompt?: string;
}

export interface LessonResponse {
  id: string;
  url: string;
  code: string;
  summary: string;
}

export interface LessonListItem extends LessonResponse {
  topic: string;
  model: string;
  format: string;
  created_at: string;
}

export interface GenerationStatus {
    status: 'initializing' | 'loading_context' | 'generating' | 'rendering' | 'finalizing' | 'complete' | 'error';
    message: string;
    progress: number;
    result?: LessonResponse;
}

export async function createLesson(request: LessonRequest): Promise<LessonResponse> {
    // We use internal /api/ routes to proxy requests and handle CORS on the server side
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

export function generateLessonStreaming(
    request: LessonRequest,
    onStatus: (status: GenerationStatus) => void,
    onError: (error: string) => void
) {
    const params = new URLSearchParams();
    if (request.topic) params.append('topic', request.topic);
    if (request.model) params.append('model', request.model);
    if (request.format) params.append('format', request.format);
    if (request.lesson_id) params.append('lesson_id', request.lesson_id);
    if (request.prompt) params.append('prompt', request.prompt);

    // EventSource establishes a unidirectional stream for real-time progress updates without the overhead of WebSockets
    // Note: EventSource only supports GET requests, so payload must be URL-encoded parameters
    const eventSource = new EventSource(`http://localhost:8000/content/lesson/generate?${params.toString()}`);

    eventSource.onmessage = (event) => {
        try {
            const data: GenerationStatus = JSON.parse(event.data);
            onStatus(data);
            
            // Explicitly close the stream to prevent memory leaks and redundant reconnections on success/failure
            if (data.status === 'complete' || data.status === 'error') {
                eventSource.close();
            }
        } catch (err) {
            console.error('Failed to parse status update:', err);
            onError('Internal Error: Failed to parse status update.');
            eventSource.close();
        }
    };

    eventSource.onerror = (error) => {
        console.error('EventSource Error:', error);
        onError('Connection Error: Failed to generate lesson.');
        eventSource.close();
    };

    // Return a cleanup function for React's useEffect to handle unmounting
    return () => eventSource.close();
}

export async function getLesson(topic: string, model: string, format: string): Promise<LessonResponse> {
    // Encodes query parameters to safely handle special characters in topics
    const params = new URLSearchParams({ topic, model, format });
    const response = await fetch(`/api/lesson?${params.toString()}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get lesson');
    }

    return response.json();
}

export async function fetchLessons(): Promise<LessonListItem[]> {
    const response = await fetch('/api/lessons', {
        method: 'GET',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lessons');
    }
    
    return response.json();
}

export async function deleteLesson(lessonId: string): Promise<void> {
    // Calls the internal proxy to perform a destructive deletion on the backend
    const response = await fetch(`/api/lesson?id=${lessonId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete lesson');
    }
}

export async function renameLesson(lessonId: string, newTitle: string): Promise<void> {
    const response = await fetch(`/api/lesson?id=${lessonId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to rename lesson');
    }
}
