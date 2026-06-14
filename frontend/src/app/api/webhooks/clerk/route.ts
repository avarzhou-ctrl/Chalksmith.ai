import { verifyWebhook } from '@clerk/nextjs/webhooks';
import { WebhookEvent } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';

function getBackendUrl() {
  const configuredUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL;

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, '');
  }

  if (process.env.NODE_ENV !== 'production') {
    return 'http://localhost:8000';
  }

  return null;
}

function getPrimaryEmail(data: WebhookEvent['data']) {
  if (!('email_addresses' in data) || !Array.isArray(data.email_addresses)) {
    return null;
  }

  const primaryEmailAddress = data.email_addresses.find(
    (emailAddress) => emailAddress.id === data.primary_email_address_id
  );

  return primaryEmailAddress?.email_address ?? data.email_addresses[0]?.email_address ?? null;
}

export async function POST(req: NextRequest) {
  let evt: WebhookEvent;

  // Verify the payload using the Clerk helper
  try {
    evt = await verifyWebhook(req) as WebhookEvent;
  } catch (err) {
    console.error('Error verifying webhook:', err);
    return new Response('Error verifying webhook', { status: 400 });
  }

  // Handle the creation or update event
  const eventType = evt.type;
  if (eventType === 'user.created' || eventType === 'user.updated') {
    const { id } = evt.data;
    const primaryEmail = getPrimaryEmail(evt.data);

    if (!primaryEmail) {
      console.error('Webhook Error: No email address found for user', id);
      return new Response('Error occured -- no email address', { status: 400 });
    }

    const API_BASE_URL = getBackendUrl();
    const INTERNAL_BACKEND_SECRET = process.env.INTERNAL_BACKEND_SECRET;

    if (!API_BASE_URL) {
      console.error('Webhook Error: API_URL or NEXT_PUBLIC_API_URL is required in production');
      return new Response('Webhook backend URL is not configured', { status: 500 });
    }

    if (!INTERNAL_BACKEND_SECRET) {
      console.error('Webhook Error: INTERNAL_BACKEND_SECRET is not configured');
      return new Response('Webhook backend secret is not configured', { status: 500 });
    }

    // Send the data to your FastAPI backend to register the user in Neon
    try {
      const response = await fetch(`${API_BASE_URL}/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Chalksmith-Secret': INTERNAL_BACKEND_SECRET,
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
