import { NextResponse, type NextRequest } from 'next/server';

const APP_HOST = 'app.chalksmith.ai';
const MARKETING_HOSTS = new Set(['chalksmith.ai', 'www.chalksmith.ai']);

export default function proxy(request: NextRequest) {
  const url = request.nextUrl.clone();
  const host = request.headers.get('host')?.split(':')[0];
  const pathname = url.pathname;

  if (host && MARKETING_HOSTS.has(host) && pathname === '/generation') {
    const destination = new URL('/', request.url);
    destination.hostname = APP_HOST;
    destination.protocol = 'https:';
    destination.search = url.search;
    return NextResponse.redirect(destination);
  }
  if (host && MARKETING_HOSTS.has(host) && pathname === '/dashboard') {
    const destination = new URL('/home', request.url);
    destination.hostname = APP_HOST;
    destination.protocol = 'https:';
    destination.search = url.search;
    return NextResponse.redirect(destination);
  }
  if (host === APP_HOST) {
    if (pathname === '/') {
      url.pathname = '/generation';
      return NextResponse.rewrite(url);
    }
    if (pathname === '/home') {
      url.pathname = '/dashboard';
      return NextResponse.rewrite(url);
    }
    if (pathname === '/generation') {
      url.pathname = '/';
      return NextResponse.redirect(url);
    }
    if (pathname === '/dashboard') {
      url.pathname = '/home';
      return NextResponse.redirect(url);
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)'],
};
