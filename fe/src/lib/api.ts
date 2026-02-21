// fe/src/lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LessonRequest {
  topic: string;
  model: string;
  format: 'manim' | 'p5.js' | 'reveal.js';
}

export interface LessonResponse {
  url: string;
  code: string;
}

export async function createLesson(request: LessonRequest): Promise<LessonResponse> {
  console.log('API Request:', { url: `${API_BASE_URL}/content/lesson`, request });
  try {
    const response = await fetch(`${API_BASE_URL}/content/lesson`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    console.log('API Response status:', response.status);

    if (!response.ok) {
      const error = await response.json();
      console.error('API Error details:', error);
      throw new Error(error.detail || `Failed to create lesson: ${response.status}`);
    }

    const data = await response.json();
    console.log('API Success data:', data);
    return data;
  } catch (err) {
    console.error('Fetch error:', err);
    throw err;
  }
}

export async function getLesson(topic: string, model: string, format: string): Promise<LessonResponse> {
  const params = new URLSearchParams({ topic, model, format });
  const response = await fetch(`${API_BASE_URL}/content/lesson?${params.toString()}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get lesson');
  }

  return response.json();
}
