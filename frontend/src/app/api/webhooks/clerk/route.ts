import { Webhook } from 'svix';
import { headers } from 'next/headers';
import { WebhookEvent } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

  if (!WEBHOOK_SECRET) {
    throw new Error('Please add CLERK_WEBHOOK_SECRET from Clerk Dashboard to .env or .env.local');
  }

  // Get the headers for verification
  const headerPayload = await headers();
  const svix_id = headerPayload.get('svix-id');
  const svix_timestamp = headerPayload.get('svix-timestamp');
  const svix_signature = headerPayload.get('svix-signature');

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return new Response('Error occured -- no svix headers', { status: 400 });
  }

  // Get the body
  const payload = await req.json();
  const body = JSON.stringify(payload);

  // Create a new Svix instance with your secret
  const wh = new Webhook(WEBHOOK_SECRET);
  let evt: WebhookEvent;

  // Verify the payload
  try {
    evt = wh.verify(body, {
      'svix-id': svix_id,
      'svix-timestamp': svix_timestamp,
      'svix-signature': svix_signature,
    }) as WebhookEvent;
  } catch (err) {
    console.error('Error verifying webhook:', err);
    return new Response('Error occured', { status: 400 });
  }

  // Handle the creation or update event
  const eventType = evt.type;
  if (eventType === 'user.created' || eventType === 'user.updated') {
    const { id, email_addresses } = evt.data;
    const primaryEmail = email_addresses[0]?.email_address;

    if (!primaryEmail) {
      console.error('Webhook Error: No email address found for user', id);
      return new Response('Error occured -- no email address', { status: 400 });
    }

    const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    // Send the data to your FastAPI backend to register the user in Neon
    try {
      const response = await fetch(`${API_BASE_URL}/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Chalksmith-Secret': process.env.INTERNAL_BACKEND_SECRET || '',
        },
        body: JSON.stringify({
          id: id,
          email: primaryEmail,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Failed to sync user to FastAPI: ${response.status} ${errorText}`);
        return new Response(`Database sync failed: ${response.status}`, { status: 500 });
      }

      console.log(`Successfully synced user ${id} to backend`);
    } catch (error) {
      console.error('Failed to sync user to FastAPI (Network Error):', error);
      return new Response('Database sync failed', { status: 500 });
    }
  }

  return NextResponse.json({ success: true }, { status: 200 });
}