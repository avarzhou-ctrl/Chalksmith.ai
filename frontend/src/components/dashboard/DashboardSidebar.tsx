'use client';

import {
  Folder,
  FolderOpen,
  FolderPlus,
  Globe2,
  PanelLeft,
  PencilLine,
  Plus,
  Search,
  Trash2,
  TriangleAlert,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import type { LessonFolder } from '@/lib/types/api';

interface DashboardSidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

interface FolderEditorState {
  mode: 'create' | 'rename';
  parentId: string | null;
  folderId: string | null;
  name: string;
}

interface FolderBranchProps {
  folders: LessonFolder[];
  parentId: string | null;
  selectedFolderId: string | null;
  onSelect: (folderId: string) => void;
  onCreate: (parentId: string) => void;
  onRename: (folder: LessonFolder) => void;
  onDelete: (folder: LessonFolder) => void;
}

function FolderBranch({
  folders,
  parentId,
  selectedFolderId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}: FolderBranchProps) {
  const children = folders
    .filter((folder) => folder.parent_id === parentId)
    .sort((left, right) => left.name.localeCompare(right.name));

  if (!children.length) return null;

  return (
    <ul className={parentId ? 'ml-4 border-l border-border pl-2' : 'mt-1'}>
      {children.map((folder) => {
        const hasChildren = folders.some((candidate) => candidate.parent_id === folder.id);
        const isSelected = selectedFolderId === folder.id;
        return (
          <li key={folder.id}>
            <section
              className={`group flex min-h-9 items-center rounded-md transition-colors ${
                isSelected ? 'bg-accent text-primary-text' : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(folder.id)}
                className="flex min-w-0 flex-1 items-center gap-2 px-2 py-2 text-left text-sm"
                title={folder.name}
              >
                {isSelected ? <FolderOpen className="shrink-0" size={16} /> : <Folder className="shrink-0" size={16} />}
                <span className="truncate">{folder.name}</span>
              </button>
              <span className="mr-1 hidden shrink-0 items-center group-hover:flex group-focus-within:flex">
                <button type="button" onClick={() => onCreate(folder.id)} className="rounded p-1 hover:bg-stone-950/30" title={`Add subfolder to ${folder.name}`}>
                  <Plus size={14} />
                </button>
                <button type="button" onClick={() => onRename(folder)} className="rounded p-1 hover:bg-stone-950/30" title={`Rename ${folder.name}`}>
                  <PencilLine size={14} />
                </button>
                <button
                  type="button"
                  disabled={hasChildren}
                  onClick={() => onDelete(folder)}
                  className="rounded p-1 hover:bg-stone-950/30 disabled:cursor-not-allowed disabled:opacity-30"
                  title={hasChildren ? 'Delete subfolders first' : `Delete ${folder.name}`}
                >
                  <Trash2 size={14} />
                </button>
              </span>
            </section>
            <FolderBranch
              folders={folders}
              parentId={folder.id}
              selectedFolderId={selectedFolderId}
              onSelect={onSelect}
              onCreate={onCreate}
              onRename={onRename}
              onDelete={onDelete}
            />
          </li>
        );
      })}
    </ul>
  );
}

export default function DashboardSidebar({ isCollapsed, onToggle }: DashboardSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const {
    folders,
    isLoading,
    error: foldersError,
    selectedFolderId,
    selectFolder,
    createFolder,
    renameFolder,
    deleteFolder,
  } = useLessonFolders();
  const [editor, setEditor] = useState<FolderEditorState | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<LessonFolder | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const isLessonsPath = pathname === '/dashboard' || pathname === '/home';
  const isPublishedPath = pathname === '/dashboard/published';

  const dashboardHref = (folderId: string | null) => (
    folderId ? `/dashboard?folder=${encodeURIComponent(folderId)}` : '/dashboard'
  );

  const selectLessons = (folderId: string | null) => {
    selectFolder(folderId);
    router.push(dashboardHref(folderId));
  };

  const openCreate = (parentId: string | null) => {
    setActionError(null);
    setEditor({ mode: 'create', parentId, folderId: null, name: '' });
  };

  const openRename = (folder: LessonFolder) => {
    setActionError(null);
    setEditor({ mode: 'rename', parentId: folder.parent_id, folderId: folder.id, name: folder.name });
  };

  const saveFolder = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editor?.name.trim()) return;
    try {
      setIsSaving(true);
      setActionError(null);
      if (editor.mode === 'create') {
        await createFolder(editor.name.trim(), editor.parentId);
      } else if (editor.folderId) {
        await renameFolder(editor.folderId, editor.name.trim());
      }
      setEditor(null);
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : 'Failed to save folder.');
    } finally {
      setIsSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const parentId = deleteTarget.parent_id;
    const wasSelected = selectedFolderId === deleteTarget.id;
    try {
      setIsSaving(true);
      setActionError(null);
      await deleteFolder(deleteTarget.id);
      setDeleteTarget(null);
      if (wasSelected) router.replace(dashboardHref(parentId));
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : 'Failed to delete folder.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="relative flex h-full w-full flex-col bg-secondary-bg px-4 pb-2 pt-4">
      <header className="mb-3 flex h-10 items-center justify-between">
        {!isCollapsed ? (
          <>
            <a href="https://chalksmith.ai/" className="flex min-w-0 items-center" aria-label="Chalksmith.ai home">
              <span className="mr-3 flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl">
                <img src="/logo.png" alt="" className="h-8 w-8 object-contain" />
              </span>
              <span className="animate-in truncate text-xl font-bold tracking-tight text-primary-text fade-in duration-300">Chalksmith.ai</span>
            </a>
            <button type="button" className="ml-2 shrink-0 rounded-lg p-2 text-secondary-text transition-all duration-300 hover:bg-surface/50" title="Collapse sidebar" onClick={onToggle}>
              <PanelLeft size={20} />
            </button>
          </>
        ) : (
          <button type="button" className="mx-auto shrink-0 rounded-lg p-2 text-secondary-text transition-all duration-300 hover:bg-surface/50" title="Expand sidebar" onClick={onToggle}>
            <PanelLeft size={20} />
          </button>
        )}
      </header>

      <nav className={`flex min-h-0 flex-1 flex-col gap-2 ${isCollapsed ? 'items-center' : ''}`}>
        <Link
          href="/dashboard/search"
          className={`group flex w-full items-center rounded-lg transition-colors ${
            pathname === '/dashboard/search' ? 'bg-surface text-primary-text' : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          } ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
          title={isCollapsed ? 'Search' : undefined}
        >
          <Search size={20} className={isCollapsed ? '' : 'mr-3'} />
          {!isCollapsed && <span className="text-sm font-medium">Search</span>}
        </Link>

        <Link
          href="/dashboard/published"
          className={`group flex w-full items-center rounded-lg transition-colors ${
            isPublishedPath ? 'bg-surface text-primary-text' : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          } ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
          title={isCollapsed ? 'Published Lessons' : undefined}
        >
          <Globe2 size={20} className={isCollapsed ? '' : 'mr-3'} />
          {!isCollapsed && <span className="text-sm font-medium">Published Lessons</span>}
        </Link>

        <section className="min-h-0 w-full overflow-y-auto">
          <span className={`group flex w-full items-center rounded-lg transition-colors ${
            isLessonsPath && selectedFolderId === null
              ? 'bg-surface text-primary-text'
              : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          }`}>
            <button
              type="button"
              onClick={() => selectLessons(null)}
              className={`flex min-w-0 flex-1 items-center rounded-lg ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
              title={isCollapsed ? 'Lessons' : undefined}
            >
              {isLessonsPath && selectedFolderId === null ? <FolderOpen size={20} /> : <Folder size={20} />}
              {!isCollapsed && <span className="ml-3 truncate text-sm font-medium">Lessons</span>}
            </button>
            {!isCollapsed && (
              <button type="button" onClick={() => openCreate(null)} className="mr-2 rounded-md p-1.5 text-current hover:bg-primary-text/10" title="Add folder">
                <FolderPlus size={18} />
              </button>
            )}
          </span>

          {!isCollapsed && (
            <>
              {isLoading && <p className="px-3 py-2 text-xs text-secondary-text">Loading folders...</p>}
              {foldersError && <p className="px-3 py-2 text-xs text-red-300">{foldersError}</p>}
              <FolderBranch
                folders={folders}
                parentId={null}
                selectedFolderId={isLessonsPath ? selectedFolderId : null}
                onSelect={(folderId) => selectLessons(folderId)}
                onCreate={openCreate}
                onRename={openRename}
                onDelete={(folder) => {
                  setActionError(null);
                  setDeleteTarget(folder);
                }}
              />
            </>
          )}
        </section>
      </nav>

      <Modal isOpen={editor !== null} onClose={() => setEditor(null)} title={editor?.mode === 'rename' ? 'Rename folder' : 'Create folder'}>
        <form onSubmit={saveFolder} className="text-left">
          <label className="text-sm font-medium text-primary-text" htmlFor="folder-name">Folder name</label>
          <input
            id="folder-name"
            autoFocus
            maxLength={100}
            value={editor?.name ?? ''}
            onChange={(event) => setEditor((current) => current ? { ...current, name: event.target.value } : current)}
            className="mt-2 h-11 w-full rounded-lg border border-border bg-primary-bg px-3 text-primary-text outline-none focus:border-accent"
          />
          {actionError && <p className="mt-3 text-sm text-red-300">{actionError}</p>}
          <span className="mt-6 flex justify-end gap-3">
            <Button type="button" variant="secondary" onClick={() => setEditor(null)}>Cancel</Button>
            <Button type="submit" disabled={isSaving || !editor?.name.trim()}>{isSaving ? 'Saving...' : 'Save'}</Button>
          </span>
        </form>
      </Modal>

      <Modal isOpen={deleteTarget !== null} onClose={() => setDeleteTarget(null)} title="Delete folder?">
        <section className="flex flex-col items-center">
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10">
            <TriangleAlert className="text-accent" size={24} />
          </span>
          <p>Lessons in <strong className="text-primary-text">{deleteTarget?.name}</strong> will move to its parent folder.</p>
          {actionError && <p className="mt-3 text-sm text-red-300">{actionError}</p>}
          <span className="mt-6 flex w-full gap-3">
            <Button type="button" variant="secondary" className="w-full" onClick={() => setDeleteTarget(null)}>Cancel</Button>
            <Button type="button" className="w-full" disabled={isSaving} onClick={() => void confirmDelete()}>{isSaving ? 'Deleting...' : 'Delete'}</Button>
          </span>
        </section>
      </Modal>
    </section>
  );
}
