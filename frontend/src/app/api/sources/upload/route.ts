import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 });
  }

  const backendUrl = `${API_BASE_URL}/sources/upload`;
  
  const backendFormData = new FormData();
  backendFormData.append('file', file, file.name);

  try {
    const headers = {
      'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
    };

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: headers,
      body: backendFormData,
    });

    const responseText = await response.text();
    const data = safeJson(responseText) ?? { detail: responseText };

    if (!response.ok) {
      return NextResponse.json({ error: data }, { status: response.status });
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to upload file to backend' }, { status: 500 });
  }
}

function safeJson(value: string) {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}
