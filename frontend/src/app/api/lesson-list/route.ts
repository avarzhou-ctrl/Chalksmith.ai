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
    const upstreamUrl = new URL(`${API_BASE_URL}/content/lessons`);
    searchParams.forEach((value, key) => {
      upstreamUrl.searchParams.set(key, value);
    });

    const response = await fetch(upstreamUrl.toString(), {
      cache: 'no-store',
      headers: {
        'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
        'X-User-Id': userId,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error('Lessons API Error:', err);
    return NextResponse.json({ detail: 'Internal Server Error' }, { status: 500 });
  }
}
