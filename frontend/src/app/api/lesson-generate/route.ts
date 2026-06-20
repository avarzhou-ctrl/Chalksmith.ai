import { getProxyAuthUserId } from '@/lib/auth-headers';
import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    const proxyUserId = getProxyAuthUserId(request);
    const { userId: clerkUserId } = await auth();
    const userId = proxyUserId || clerkUserId;

    if (!userId) {
      return createSseErrorResponse('Unauthorized', 401);
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
      return createSseErrorResponse(getErrorMessage(error), response.status);
    }

    if (!response.body) {
      return createSseErrorResponse('Generation stream unavailable', 502);
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
    return createSseErrorResponse('Internal Server Error', 500);
  }
}

function safeJson(value: string) {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function getErrorMessage(error: unknown) {
  if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
    return error.detail;
  }

  if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string') {
    return error.message;
  }

  return 'Generation stream failed';
}

function createSseErrorResponse(message: string, upstreamStatus: number) {
  const payload = {
    status: 'error',
    message,
    progress: 0,
    upstreamStatus,
  };

  return new Response(`data: ${JSON.stringify(payload)}\n\n`, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  });
}
