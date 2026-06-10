import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    // 1. Double check the edge-verified identity session
    const { userId } = await auth();
    if (!userId) {
      return new NextResponse("Unauthorized Account Access", { status: 401 });
    }

    const body = await request.json();

    // 2. Forward the payload to Render, passing your server-side secret token
    const backendResponse = await fetch(`${API_URL}/lesson`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // A dedicated secret key shared only between Vercel and Render
        'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
        'X-User-Id': userId // Pass along the validated user ID string
      },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error("Proxy route execution crash:", error);
    return new NextResponse("Internal Server Execution Error", { status: 500 });
  }
}