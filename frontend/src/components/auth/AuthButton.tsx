'use client';

import Link from 'next/link';
import { LogIn, LogOut, UserRound } from 'lucide-react';
import { useState, type FormEvent } from 'react';

import { useAuth } from '@/components/auth/AuthProvider';

export function AuthButton() {
  const { user, loading, openAuth, logOut, linkGoogle, linkMicrosoft, linkEmail } = useAuth();
  const [message, setMessage] = useState('');
  const [showEmailLink, setShowEmailLink] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function link(action: () => Promise<void>) {
    try {
      await action();
      setMessage('Login method linked.');
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : 'Could not link this login method.');
    }
  }
  async function submitEmailLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await link(() => linkEmail(email, password));
    setPassword('');
  }
  if (loading) return <span className="size-10 animate-pulse rounded-full bg-stone-800" />;
  if (!user) {
    return <button type="button" onClick={openAuth} className="flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-stone-950 hover:bg-amber-500">Start Free<LogIn className="size-4" /></button>;
  }
  const linkedProviders = new Set(user.providerData.map((provider) => provider.providerId));
  return (
    <details className="relative">
      <summary className="grid size-10 cursor-pointer list-none place-items-center rounded-full border border-stone-700 bg-stone-800 text-stone-100 hover:border-amber-600" aria-label="Open account menu">
        {user.photoURL ? <img src={user.photoURL} alt="" className="size-9 rounded-full object-cover" /> : <UserRound className="size-5" />}
      </summary>
      <section className="absolute right-0 z-50 mt-2 grid w-64 gap-1 rounded-xl border border-stone-700 bg-stone-900 p-2 text-sm shadow-xl">
        <Link href="/dashboard" className="rounded-lg px-3 py-2 text-stone-200 hover:bg-stone-800">Open dashboard</Link>
        {!linkedProviders.has('google.com') && <button type="button" onClick={() => void link(linkGoogle)} className="rounded-lg px-3 py-2 text-left text-stone-300 hover:bg-stone-800">Link Google login</button>}
        {!linkedProviders.has('microsoft.com') && <button type="button" onClick={() => void link(linkMicrosoft)} className="rounded-lg px-3 py-2 text-left text-stone-300 hover:bg-stone-800">Link Microsoft login</button>}
        {!linkedProviders.has('password') && <button type="button" onClick={() => {
          setEmail(user.email ?? '');
          setShowEmailLink((current) => !current);
        }} className="rounded-lg px-3 py-2 text-left text-stone-300 hover:bg-stone-800">Link email login</button>}
        {!linkedProviders.has('password') && showEmailLink && (
          <form onSubmit={(event) => void submitEmailLink(event)} className="grid gap-2 border-t border-stone-800 px-2 py-2">
            <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email" className="rounded-lg border border-stone-700 bg-stone-950 p-2 text-stone-50 outline-none focus:border-amber-600" />
            <input required minLength={6} type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Password" className="rounded-lg border border-stone-700 bg-stone-950 p-2 text-stone-50 outline-none focus:border-amber-600" />
            <button className="rounded-lg bg-amber-600 p-2 font-medium text-stone-950 hover:bg-amber-500">Link email</button>
          </form>
        )}
        {message && <p className="px-3 py-1 text-xs text-stone-400" role="status">{message}</p>}
        <button type="button" onClick={() => void logOut()} className="flex items-center gap-2 rounded-lg px-3 py-2 text-left text-stone-300 hover:bg-stone-800"><LogOut className="size-4" />Sign out</button>
      </section>
    </details>
  );
}
