import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const file = formData.get('file') as File;

  if (!file) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 });
  }

  const backendUrl = `${process.env.API_BASE_URL}/sources/upload`;
  console.log('Backend URL:', backendUrl);
  
  const backendFormData = new FormData();
  backendFormData.append('file', file, file.name);

  try {
    const headers = {
      'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
    };
    console.log('Request headers to backend:', headers);

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: headers,
      body: backendFormData,
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json({ error: data }, { status: response.status });
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to upload file to backend' }, { status: 500 });
  }
}
