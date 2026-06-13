import { getProxyAuthUserId } from '@/lib/auth-headers';
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    const userId = getProxyAuthUserId(request);
    if (!userId) {
      return NextResponse.json({ detail: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const upstreamUrl = new URL('/content/lesson/generate', API_BASE_URL);
    searchParams.forEach((value, key) => {
      upstreamUrl.searchParams.append(key, value);
    });

    const response = await fetch(upstreamUrl, {
      cache: 'no-store',
      headers: {
        Accept: 'text/event-stream',
        'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
        'X-User-Id': userId,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      const error = safeJson(errorText) ?? { detail: errorText || 'Generation stream failed' };
      return NextResponse.json(error, { status: response.status });
    }

    if (!response.body) {
      return NextResponse.json({ detail: 'Generation stream unavailable' }, { status: 502 });
    }

    return new Response(response.body, {
      status: response.status,
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  } catch (err) {
    console.error('Generation Stream API Error:', err);
    return NextResponse.json({ detail: 'Internal Server Error' }, { status: 500 });
  }
}

function safeJson(value: string) {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}
