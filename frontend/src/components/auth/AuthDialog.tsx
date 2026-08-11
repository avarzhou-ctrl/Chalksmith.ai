'use client';

import { useState, type FormEvent } from 'react';
import { X } from 'lucide-react';

import { useAuth } from '@/components/auth/AuthProvider';

export function AuthDialog({ open }: { open: boolean }) {
  const auth = useAuth();
  const [mode, setMode] = useState<'sign-in' | 'register'>('sign-in');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  if (!open) return null;

  async function run(action: () => Promise<void>, successMessage = '') {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      setNotice(successMessage);
    } catch (caught) {
      const code = typeof caught === 'object' && caught && 'code' in caught ? String(caught.code) : '';
      if (code === 'auth/account-exists-with-different-credential') {
        setError('An account already uses this email. Sign in with its original method here; the new login method will then be linked automatically.');
      } else if (code === 'auth/invalid-credential') {
        setError('The email or password is incorrect.');
      } else if (code === 'auth/popup-closed-by-user') {
        setError('The sign-in window was closed before login completed.');
      } else {
        setError(caught instanceof Error ? caught.message : 'Sign-in failed.');
      }
    } finally {
      setBusy(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void run(() => mode === 'register'
      ? auth.registerWithEmail(email, password)
      : auth.signInWithEmail(email, password));
  }

  return (
    <section className="fixed inset-0 z-[100] grid place-items-center bg-stone-950/80 p-4" aria-modal="true" role="dialog" aria-label="Sign in">
      <article className="relative w-full max-w-md rounded-2xl border border-stone-700 bg-stone-900 p-6 shadow-2xl">
        <button type="button" onClick={auth.closeAuth} className="absolute right-4 top-4 rounded-lg p-2 text-stone-400 hover:bg-stone-800 hover:text-stone-50" aria-label="Close sign in">
          <X className="size-5" />
        </button>
        <h2 className="text-2xl font-semibold text-stone-50">{mode === 'register' ? 'Create an account' : 'Welcome back'}</h2>
        <p className="mt-2 text-sm text-stone-400">Use Google, Microsoft, or a Chalksmith email account.</p>

        <section className="mt-6 grid gap-3">
          <button type="button" disabled={busy} onClick={() => void run(auth.signInWithGoogle)} className="rounded-lg border border-stone-700 bg-stone-800 px-4 py-3 text-sm font-medium text-stone-50 hover:border-amber-600 disabled:opacity-50">Continue with Google</button>
          <button type="button" disabled={busy} onClick={() => void run(auth.signInWithMicrosoft)} className="rounded-lg border border-stone-700 bg-stone-800 px-4 py-3 text-sm font-medium text-stone-50 hover:border-amber-600 disabled:opacity-50">Continue with Microsoft</button>
        </section>

        <p className="my-5 text-center text-xs uppercase tracking-widest text-stone-500">or email</p>
        <form onSubmit={submit} className="grid gap-3">
          <label className="grid gap-1 text-sm text-stone-300">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="rounded-lg border border-stone-700 bg-stone-950 p-3 text-stone-50 outline-none focus:border-amber-600" /></label>
          <label className="grid gap-1 text-sm text-stone-300">Password<input required minLength={6} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="rounded-lg border border-stone-700 bg-stone-950 p-3 text-stone-50 outline-none focus:border-amber-600" /></label>
          {error && <p className="text-sm text-red-400" role="alert">{error}</p>}
          {notice && <p className="text-sm text-emerald-400" role="status">{notice}</p>}
          <button disabled={busy} className="mt-2 rounded-lg bg-amber-600 px-4 py-3 font-medium text-stone-950 hover:bg-amber-500 disabled:opacity-50">{busy ? 'Please wait…' : mode === 'register' ? 'Create account' : 'Sign in'}</button>
        </form>
        <section className="mt-4 flex justify-between text-sm">
          <button type="button" onClick={() => setMode(mode === 'register' ? 'sign-in' : 'register')} className="text-amber-500 hover:text-amber-400">{mode === 'register' ? 'Already have an account?' : 'Create an account'}</button>
          {mode === 'sign-in' && <button type="button" onClick={() => void run(() => auth.resetPassword(email), 'Password reset email sent.')} disabled={!email || busy} className="text-stone-400 hover:text-stone-200 disabled:opacity-40">Reset password</button>}
        </section>
        <p className="mt-6 text-xs text-stone-500">By creating an account, you confirm you are at least 13 years old.</p>
      </article>
    </section>
  );
}
