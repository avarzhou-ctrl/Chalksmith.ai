import { getProxyAuthUserId } from '@/lib/auth-headers';
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const userId = getProxyAuthUserId(request);
    if (!userId) {
      return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const lessonId = searchParams.get('id');

    if (!lessonId) {
      return NextResponse.json({ detail: 'Lesson ID is required' }, { status: 400 });
    }

    const response = await fetch(`${API_BASE_URL}/content/export?id=${lessonId}`, {
      headers: {
        'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
        'X-User-Id': userId,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      return NextResponse.json(error, { status: response.status });
    }

    // Proxy the file content back to the client
    const headers = new Headers();
    
    // Forward relevant headers from the backend response
    const contentType = response.headers.get('Content-Type');
    if (contentType) headers.set('Content-Type', contentType);
    
    const contentDisposition = response.headers.get('Content-Disposition');
    if (contentDisposition) headers.set('Content-Disposition', contentDisposition);

    return new NextResponse(response.body, {
      status: 200,
      headers,
    });
  } catch (err) {
    console.error('Export API Error:', err);
    return NextResponse.json({ detail: 'Internal Server Error' }, { status: 500 });
  }
}
