'use client';

import {
  EmailAuthProvider,
  GoogleAuthProvider,
  OAuthProvider,
  createUserWithEmailAndPassword,
  linkWithCredential,
  linkWithPopup,
  onIdTokenChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type AuthCredential,
  type User,
  type UserCredential,
} from 'firebase/auth';
import { FirebaseError } from 'firebase/app';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { AuthDialog } from '@/components/auth/AuthDialog';
import { getFirebaseAuth } from '@/lib/firebase/client';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  openAuth: () => void;
  closeAuth: () => void;
  getIdToken: (forceRefresh?: boolean) => Promise<string | null>;
  signInWithGoogle: () => Promise<void>;
  signInWithMicrosoft: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  registerWithEmail: (email: string, password: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  linkGoogle: () => Promise<void>;
  linkMicrosoft: () => Promise<void>;
  linkEmail: (email: string, password: string) => Promise<void>;
  logOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [pendingCredential, setPendingCredential] = useState<AuthCredential | null>(null);

  useEffect(() => {
    try {
      return onIdTokenChanged(getFirebaseAuth(), (nextUser) => {
        setUser(nextUser);
        setLoading(false);
      });
    } catch {
      setLoading(false);
      return undefined;
    }
  }, []);

  const finish = useCallback(async (action: () => Promise<UserCredential>) => {
    const result = await action();
    if (pendingCredential) {
      await linkWithCredential(result.user, pendingCredential);
      setPendingCredential(null);
    }
    setDialogOpen(false);
  }, [pendingCredential]);

  const signInWithProvider = useCallback(async (
    provider: GoogleAuthProvider | OAuthProvider,
  ): Promise<UserCredential> => {
    try {
      return await signInWithPopup(getFirebaseAuth(), provider);
    } catch (error) {
      if (
        error instanceof FirebaseError
        && error.code === 'auth/account-exists-with-different-credential'
      ) {
        const credential = provider instanceof GoogleAuthProvider
          ? GoogleAuthProvider.credentialFromError(error)
          : OAuthProvider.credentialFromError(error);
        if (credential) setPendingCredential(credential);
      }
      throw error;
    }
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    openAuth: () => setDialogOpen(true),
    closeAuth: () => setDialogOpen(false),
    getIdToken: async (forceRefresh = false) => user?.getIdToken(forceRefresh) ?? null,
    signInWithGoogle: () => finish(() => signInWithProvider(new GoogleAuthProvider())),
    signInWithMicrosoft: () => finish(() => signInWithProvider(new OAuthProvider('microsoft.com'))),
    signInWithEmail: (email, password) => finish(() => signInWithEmailAndPassword(getFirebaseAuth(), email, password)),
    registerWithEmail: (email, password) => finish(() => createUserWithEmailAndPassword(getFirebaseAuth(), email, password)),
    resetPassword: (email) => sendPasswordResetEmail(getFirebaseAuth(), email),
    linkGoogle: async () => {
      if (!user) throw new Error('Sign in before linking another login method.');
      await linkWithPopup(user, new GoogleAuthProvider());
    },
    linkMicrosoft: async () => {
      if (!user) throw new Error('Sign in before linking another login method.');
      await linkWithPopup(user, new OAuthProvider('microsoft.com'));
    },
    linkEmail: async (email, password) => {
      if (!user) throw new Error('Sign in before linking another login method.');
      await linkWithCredential(user, EmailAuthProvider.credential(email, password));
    },
    logOut: () => signOut(getFirebaseAuth()),
  }), [finish, loading, signInWithProvider, user]);

  return (
    <AuthContext.Provider value={value}>
      {children}
      <AuthDialog open={dialogOpen} />
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider.');
  return context;
}
