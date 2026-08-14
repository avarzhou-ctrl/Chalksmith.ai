import { clerkMiddleware } from '@clerk/nextjs/server';
import { NextResponse, type NextRequest } from 'next/server';

const SITE_DOMAIN = process.env.NEXT_PUBLIC_SITE_DOMAIN || 'chalksmith.ai';
const APP_HOST = `app.${SITE_DOMAIN}`;
const MARKETING_HOSTS = new Set([SITE_DOMAIN, `www.${SITE_DOMAIN}`]);

// Cloud Run terminates TLS and forwards to the container's own port, so anything
// derived from the request carries :8080 into an absolute redirect.
const appUrl = (pathname: string, search: string) => {
  const destination = new URL(pathname, `https://${APP_HOST}`);
  destination.search = search;
  return destination;
};

export default clerkMiddleware((_auth, request: NextRequest) => {
  const url = request.nextUrl.clone();
  const host = request.headers.get('host')?.split(':')[0];
  const pathname = url.pathname;

  if (host && MARKETING_HOSTS.has(host) && pathname === '/generation') {
    return NextResponse.redirect(appUrl('/generation', url.search));
  }
  if (host && MARKETING_HOSTS.has(host) && pathname === '/dashboard') {
    return NextResponse.redirect(appUrl('/home', url.search));
  }
  if (host === APP_HOST) {
    // /home is the app's landing page and its canonical URL; /generation keeps
    // its own so the app root is not two different pages.
    if (pathname === '/' || pathname === '/dashboard') {
      return NextResponse.redirect(appUrl('/home', url.search));
    }
    if (pathname === '/home') {
      url.pathname = '/dashboard';
      return NextResponse.rewrite(url);
    }
  }
  return NextResponse.next();
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
    '/__clerk/:path*',
  ],
};
