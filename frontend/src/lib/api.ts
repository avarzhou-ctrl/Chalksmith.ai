// Shared interfaces between frontend and backend to ensure type safety across the stack
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LessonRequest {
  topic: string;
  model: string;
  format: string;
  lesson_id?: string;
  prompt?: string;
  sourceFiles?: File[];
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
    const response = await fetch('/api/lesson-record', {
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
    if (request.sourceFiles?.length) {
        return generateLessonStreamingWithSources(request, onStatus, onError);
    }

    const params = new URLSearchParams();
    if (request.topic) params.append('topic', request.topic);
    if (request.model) params.append('model', request.model);
    if (request.format) params.append('format', request.format);
    if (request.lesson_id) params.append('lesson_id', request.lesson_id);
    if (request.prompt) params.append('prompt', request.prompt);

    // EventSource establishes a unidirectional stream for real-time progress updates without the overhead of WebSockets
    // Note: EventSource only supports GET requests, so payload must be URL-encoded parameters
    const eventSource = new EventSource(`/api/lesson-generate?${params.toString()}`);

    eventSource.onmessage = (event) => {
        try {
            const data: GenerationStatus = JSON.parse(event.data);

            if (data.status === 'error') {
                eventSource.close();
                onError(data.message || 'This lesson could not be generated.');
                return;
            }

            onStatus(data);
            
            // Explicitly close the stream to prevent memory leaks and redundant reconnections on success/failure
            if (data.status === 'complete') {
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

function generateLessonStreamingWithSources(
    request: LessonRequest,
    onStatus: (status: GenerationStatus) => void,
    onError: (error: string) => void
) {
    const controller = new AbortController();

    const formData = new FormData();
    formData.append('topic', request.topic);
    formData.append('model', request.model);
    formData.append('format', request.format);
    if (request.lesson_id) formData.append('lesson_id', request.lesson_id);
    if (request.prompt) formData.append('prompt', request.prompt);
    request.sourceFiles?.forEach((file) => {
        formData.append('source', file, file.name);
    });

    void (async () => {
        try {
            const response = await fetch('/api/lesson-generate', {
                method: 'POST',
                body: formData,
                signal: controller.signal,
            });

            if (!response.ok || !response.body) {
                onError('Connection Error: Failed to generate lesson.');
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const chunks = buffer.split('\n\n');
                buffer = chunks.pop() || '';

                for (const chunk of chunks) {
                    const isTerminal = processSseChunk(chunk, onStatus, onError);
                    if (isTerminal) {
                        controller.abort();
                        return;
                    }
                }
            }

            if (buffer.trim()) {
                processSseChunk(buffer, onStatus, onError);
            }
        } catch (err) {
            if (controller.signal.aborted) return;
            console.error('Fetch Stream Error:', err);
            onError('Connection Error: Failed to generate lesson.');
        }
    })();

    return () => controller.abort();
}

function processSseChunk(
    chunk: string,
    onStatus: (status: GenerationStatus) => void,
    onError: (error: string) => void
) {
    const data = chunk
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trimStart())
        .join('\n');

    if (!data) return false;

    try {
        const status: GenerationStatus = JSON.parse(data);

        if (status.status === 'error') {
            onError(status.message || 'This lesson could not be generated.');
            return true;
        }

        onStatus(status);
        return status.status === 'complete';
    } catch (err) {
        console.error('Failed to parse status update:', err);
        onError('Internal Error: Failed to parse status update.');
        return true;
    }
}

export async function getLesson(topic: string, model: string, format: string): Promise<LessonResponse> {
    // Encodes query parameters to safely handle special characters in topics
    const params = new URLSearchParams({ topic, model, format });
    const response = await fetch(`/api/lesson-record?${params.toString()}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get lesson');
    }

    return response.json();
}

export async function fetchLessonById(lessonId: string): Promise<LessonListItem> {
    const response = await fetch(`/api/lesson-record?id=${lessonId}`, {
        method: 'GET',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lesson');
    }

    return response.json();
}

export async function fetchLessons(params?: {
    q?: string;
    format?: string;
}): Promise<LessonListItem[]> {
    const searchParams = new URLSearchParams();

    if (params?.q) searchParams.set('q', params.q);
    if (params?.format) searchParams.set('format', params.format);

    const url = searchParams.toString()
        ? `/api/lesson-list?${searchParams.toString()}`
        : '/api/lesson-list';

    const response = await fetch(url, { method: 'GET' });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to fetch lessons');
    }
    
    return response.json();
}

export async function deleteLesson(lessonId: string): Promise<void> {
    // Calls the internal proxy to perform a destructive deletion on the backend
    const response = await fetch(`/api/lesson-record?id=${lessonId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete lesson');
    }
}

export async function renameLesson(lessonId: string, newTitle: string): Promise<void> {
    const response = await fetch(`/api/lesson-record?id=${lessonId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to rename lesson');
    }
}
