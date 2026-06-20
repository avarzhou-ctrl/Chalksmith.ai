import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { PROXY_AUTH_USER_ID_HEADER } from './lib/auth-headers'

const APP_HOST = 'app.chalksmith.ai'
const MARKETING_HOSTS = new Set(['chalksmith.ai', 'www.chalksmith.ai'])
const isProtectedRoute = createRouteMatcher([
  '/generation(.*)', 
  '/dashboard(.*)', 
  '/home(.*)',
  '/api/generate(.*)'
]);
const isProtectedLessonApiRoute = createRouteMatcher([
  '/api/lesson-record(.*)',
  '/api/lesson-list(.*)',
  '/api/lessons(.*)',
  '/api/lesson-export(.*)',
]);
 
export default clerkMiddleware(async (auth, request) => {
  const url = request.nextUrl.clone()
  const host = request.headers.get('host')?.split(':')[0]
  const pathname = url.pathname

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

  if (isProtectedLessonApiRoute(request)) {
    const { userId } = await auth.protect()
    const requestHeaders = new Headers(request.headers)
    requestHeaders.delete('x-user-id')
    requestHeaders.set(PROXY_AUTH_USER_ID_HEADER, userId)

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    })
  }

  if (isProtectedRoute(request)) {
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
    // Always run for API routes
    '/(api|trpc)(.*)',
    // Always run for Clerk-specific frontend API routes
    '/__clerk/(.*)',
  ],
}
