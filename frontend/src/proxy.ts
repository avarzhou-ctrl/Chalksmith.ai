import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'

const APP_HOST = 'app.chalksmith.ai'
const MARKETING_HOSTS = new Set(['chalksmith.ai', 'www.chalksmith.ai'])
const isProtectedRoute = createRouteMatcher([
  '/generation(.*)', 
  '/dashboard(.*)', 
  '/home(.*)',
  '/api/generate(.*)'
]);
 
export default clerkMiddleware(async (auth, request) => {
  const url = request.nextUrl.clone()
  const host = request.headers.get('host')?.split(':')[0]
  const pathname = url.pathname
  const isAppRoot = host === APP_HOST && pathname === '/'

  if (host && MARKETING_HOSTS.has(host)) {
    if (pathname === '/generation') {
      const redirectUrl = new URL('/', request.url)
      redirectUrl.hostname = APP_HOST
      redirectUrl.protocol = 'https:'
      redirectUrl.search = url.search
      return NextResponse.redirect(redirectUrl)
    }

    if (pathname === '/dashboard') {
      const redirectUrl = new URL('/home', request.url)
      redirectUrl.hostname = APP_HOST
      redirectUrl.protocol = 'https:'
      redirectUrl.search = url.search
      return NextResponse.redirect(redirectUrl)
    }
  }

  if (isAppRoot || isProtectedRoute(request)) {
    await auth.protect()
  }

  if (host === APP_HOST) {
    if (pathname === '/') {
      url.pathname = '/generation'
      return NextResponse.rewrite(url)
    }

    if (pathname === '/home') {
      url.pathname = '/dashboard'
      return NextResponse.rewrite(url)
    }

    if (pathname === '/generation') {
      url.pathname = '/'
      return NextResponse.redirect(url)
    }

    if (pathname === '/dashboard') {
      url.pathname = '/home'
      return NextResponse.redirect(url)
    }
  }

  return NextResponse.next()
})

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for Clerk's auto-proxy path
    '/__clerk/:path*',
    // Always run for API routes
    '/(api|trpc)(.*)'
  ],
}
