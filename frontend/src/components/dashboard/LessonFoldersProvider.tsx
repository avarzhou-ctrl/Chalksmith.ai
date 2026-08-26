'use client';

import { useAuth } from '@clerk/nextjs';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  createFolder as createFolderRequest,
  deleteFolder as deleteFolderRequest,
  listFolders,
  renameFolder as renameFolderRequest,
} from '@/lib/api/folders';
import { useApi } from '@/lib/hooks/useApi';
import type { LessonFolder } from '@/lib/types/api';

interface LessonFoldersContextValue {
  folders: LessonFolder[];
  isLoading: boolean;
  error: string | null;
  selectedFolderId: string | null;
  selectFolder: (folderId: string | null) => void;
  resolveFolderId: (folderId: string | null) => string | null;
  createFolder: (name: string, parentId: string | null) => Promise<void>;
  renameFolder: (folderId: string, name: string) => Promise<void>;
  deleteFolder: (folderId: string) => Promise<void>;
}

const LessonFoldersContext = createContext<LessonFoldersContextValue | null>(null);

export function LessonFoldersProvider({ children }: { children: React.ReactNode }) {
  const api = useApi();
  const { isLoaded, isSignedIn } = useAuth();
  const [folders, setFolders] = useState<LessonFolder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [folderRedirects, setFolderRedirects] = useState<Record<string, string | null>>({});

  useEffect(() => {
    const syncFolderFromLocation = () => {
      setSelectedFolderId(new URLSearchParams(window.location.search).get('folder'));
    };
    syncFolderFromLocation();
    window.addEventListener('popstate', syncFolderFromLocation);
    return () => window.removeEventListener('popstate', syncFolderFromLocation);
  }, []);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) {
      setIsLoading(!isLoaded);
      return;
    }
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    void listFolders(api, controller.signal)
      .then(setFolders)
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught.message : 'Failed to load folders.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [api, isLoaded, isSignedIn]);

  const selectFolder = useCallback((folderId: string | null) => {
    setSelectedFolderId(folderId);
  }, []);

  const resolveFolderId = useCallback((folderId: string | null) => {
    let current = folderId;
    const visited = new Set<string>();
    while (current && Object.prototype.hasOwnProperty.call(folderRedirects, current) && !visited.has(current)) {
      visited.add(current);
      current = folderRedirects[current];
    }
    return current;
  }, [folderRedirects]);

  const createFolder = useCallback(async (name: string, parentId: string | null) => {
    const created = await createFolderRequest(api, name, parentId);
    setFolders((current) => [...current, created]);
  }, [api]);

  const renameFolder = useCallback(async (folderId: string, name: string) => {
    const updated = await renameFolderRequest(api, folderId, name);
    setFolders((current) => current.map((folder) => folder.id === folderId ? updated : folder));
  }, [api]);

  const deleteFolder = useCallback(async (folderId: string) => {
    const folder = folders.find((candidate) => candidate.id === folderId);
    await deleteFolderRequest(api, folderId);
    setFolders((current) => current.filter((candidate) => candidate.id !== folderId));
    setFolderRedirects((current) => ({ ...current, [folderId]: folder?.parent_id ?? null }));
    setSelectedFolderId((current) => current === folderId ? folder?.parent_id ?? null : current);
  }, [api, folders]);

  const value = useMemo<LessonFoldersContextValue>(() => ({
    folders,
    isLoading,
    error,
    selectedFolderId,
    selectFolder,
    resolveFolderId,
    createFolder,
    renameFolder,
    deleteFolder,
  }), [
    createFolder,
    deleteFolder,
    error,
    folders,
    isLoading,
    renameFolder,
    resolveFolderId,
    selectFolder,
    selectedFolderId,
  ]);

  return <LessonFoldersContext.Provider value={value}>{children}</LessonFoldersContext.Provider>;
}

export function useLessonFolders() {
  const context = useContext(LessonFoldersContext);
  if (!context) throw new Error('useLessonFolders must be used within LessonFoldersProvider.');
  return context;
}
