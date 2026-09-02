'use client';

import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  FolderPlus,
  Globe2,
  LibraryBig,
  PanelLeft,
  PencilLine,
  Plus,
  Search,
  Trash2,
  TriangleAlert,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { type DragEvent, FormEvent, useState } from 'react';

import { useLessonFolders } from '@/components/dashboard/LessonFoldersProvider';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Skeleton, { SkeletonStatus } from '@/components/ui/Skeleton';
import { moveLesson } from '@/lib/api/lessons';
import { useApi } from '@/lib/hooks/useApi';
import { useLessonSets } from '@/lib/hooks/useLessonSets';
import {
  dispatchLessonMoved,
  getLessonDragData,
} from '@/lib/lesson-drag';
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
  collapsedFolderIds: Set<string>;
  onToggle: (folderId: string) => void;
  activeDropTarget: string | null;
  onDragEnter: (event: DragEvent<HTMLElement>, target: string, effect: 'copy' | 'move') => void;
  onDragLeave: (event: DragEvent<HTMLElement>, target: string) => void;
  onDrop: (event: DragEvent<HTMLElement>, folderId: string) => void;
}

function FolderBranch({
  folders,
  parentId,
  selectedFolderId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
  collapsedFolderIds,
  onToggle,
  activeDropTarget,
  onDragEnter,
  onDragLeave,
  onDrop,
}: FolderBranchProps) {
  const children = folders
    .filter((folder) => folder.parent_id === parentId)
    .sort((left, right) => left.name.localeCompare(right.name));

  if (!children.length) return null;

  return (
    <ul className="ml-4 mt-1 border-l border-border pl-2">
      {children.map((folder) => {
        const hasChildren = folders.some((candidate) => candidate.parent_id === folder.id);
        const isSelected = selectedFolderId === folder.id;
        const isCollapsed = collapsedFolderIds.has(folder.id);
        const dropTarget = `folder:${folder.id}`;
        return (
          <li key={folder.id}>
            <section
              onDragEnter={(event) => onDragEnter(event, dropTarget, 'move')}
              onDragOver={(event) => onDragEnter(event, dropTarget, 'move')}
              onDragLeave={(event) => onDragLeave(event, dropTarget)}
              onDrop={(event) => onDrop(event, folder.id)}
              className={`group flex min-h-9 items-center rounded-md border transition-colors ${
                activeDropTarget === dropTarget
                  ? 'border-accent bg-accent/20 text-primary-text'
                  : isSelected
                    ? 'border-transparent bg-surface text-primary-text'
                    : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
              }`}
            >
              {hasChildren ? (
                <button
                  type="button"
                  onClick={() => onToggle(folder.id)}
                  className="ml-1 rounded p-1 hover:bg-stone-950/30"
                  title={isCollapsed ? `Expand ${folder.name}` : `Collapse ${folder.name}`}
                  aria-label={isCollapsed ? `Expand ${folder.name}` : `Collapse ${folder.name}`}
                  aria-expanded={!isCollapsed}
                >
                  {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                </button>
              ) : <span className="ml-1 size-6" />}
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
            {!isCollapsed && (
              <FolderBranch
                folders={folders}
                parentId={folder.id}
                selectedFolderId={selectedFolderId}
                onSelect={onSelect}
                onCreate={onCreate}
                onRename={onRename}
                onDelete={onDelete}
                collapsedFolderIds={collapsedFolderIds}
                onToggle={onToggle}
                activeDropTarget={activeDropTarget}
                onDragEnter={onDragEnter}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
              />
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default function DashboardSidebar({ isCollapsed, onToggle }: DashboardSidebarProps) {
  const api = useApi();
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
  const {
    lessonSets,
    isLoading: areLessonSetsLoading,
    error: lessonSetsError,
    addLessonToSet,
  } = useLessonSets();
  const [editor, setEditor] = useState<FolderEditorState | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<LessonFolder | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [areFoldersExpanded, setAreFoldersExpanded] = useState(true);
  const [areLessonSetsExpanded, setAreLessonSetsExpanded] = useState(true);
  const [collapsedFolderIds, setCollapsedFolderIds] = useState<Set<string>>(new Set());
  const [activeDropTarget, setActiveDropTarget] = useState<string | null>(null);
  const [dropMessage, setDropMessage] = useState<string | null>(null);
  const [dropError, setDropError] = useState<string | null>(null);
  const isLessonsPath = pathname === '/dashboard' || pathname === '/home';
  const isPublishedPath = pathname === '/dashboard/published';
  const isLessonSetsIndexPath = pathname === '/dashboard/sets';

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

  const toggleFolder = (folderId: string) => {
    setCollapsedFolderIds((current) => {
      const next = new Set(current);
      if (next.has(folderId)) next.delete(folderId);
      else next.add(folderId);
      return next;
    });
  };

  const enterDropTarget = (
    event: DragEvent<HTMLElement>,
    target: string,
    effect: 'copy' | 'move',
  ) => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = effect;
    setActiveDropTarget(target);
  };

  const leaveDropTarget = (event: DragEvent<HTMLElement>, target: string) => {
    const nextTarget = event.relatedTarget as Node | null;
    if (nextTarget && event.currentTarget.contains(nextTarget)) return;
    if (activeDropTarget === target) setActiveDropTarget(null);
  };

  const dropIntoFolder = async (event: DragEvent<HTMLElement>, folderId: string | null) => {
    event.preventDefault();
    event.stopPropagation();
    const payload = getLessonDragData(event.dataTransfer);
    setActiveDropTarget(null);
    if (!payload) return;
    try {
      setDropError(null);
      setDropMessage(`Moving ${payload.title}…`);
      await moveLesson(api, payload.lessonId, folderId);
      dispatchLessonMoved({ lessonId: payload.lessonId, folderId });
      const folderName = folderId
        ? folders.find((folder) => folder.id === folderId)?.name ?? 'folder'
        : 'My Lessons';
      setDropMessage(`Moved ${payload.title} to ${folderName}.`);
    } catch (caught) {
      setDropMessage(null);
      setDropError(caught instanceof Error ? caught.message : 'Failed to move lesson.');
    }
  };

  const dropIntoLessonSet = async (event: DragEvent<HTMLElement>, lessonSetId: string) => {
    event.preventDefault();
    event.stopPropagation();
    const payload = getLessonDragData(event.dataTransfer);
    setActiveDropTarget(null);
    if (!payload) return;
    try {
      setDropError(null);
      setDropMessage(`Adding ${payload.title}…`);
      const updated = await addLessonToSet(lessonSetId, payload.lessonId);
      setDropMessage(`Added ${payload.title} to ${updated.title}.`);
    } catch (caught) {
      setDropMessage(null);
      setDropError(caught instanceof Error ? caught.message : 'Failed to add lesson to set.');
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
          className={`group flex w-full items-center rounded-lg border transition-colors ${
            pathname === '/dashboard/search' ? 'border-transparent bg-surface text-primary-text' : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          } ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
          title={isCollapsed ? 'Search' : undefined}
        >
          <Search size={20} className={isCollapsed ? '' : 'mr-3'} />
          {!isCollapsed && <span className="text-sm font-medium">Search</span>}
        </Link>

        {!isCollapsed && (
          <p className="px-3 pt-3 text-xs font-semibold uppercase tracking-wider text-secondary-text/70">My Content</p>
        )}
        <section className="min-h-0 w-full overflow-y-auto">
          <span
            onDragEnter={(event) => {
              setAreFoldersExpanded(true);
              enterDropTarget(event, 'folder:root', 'move');
            }}
            onDragOver={(event) => enterDropTarget(event, 'folder:root', 'move')}
            onDragLeave={(event) => leaveDropTarget(event, 'folder:root')}
            onDrop={(event) => void dropIntoFolder(event, null)}
            className={`group flex w-full items-center rounded-lg border transition-colors ${
              activeDropTarget === 'folder:root'
                ? 'border-accent bg-accent/20 text-primary-text'
                : isLessonsPath && selectedFolderId === null
                  ? 'border-transparent bg-surface text-primary-text'
                  : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          }`}>
            {!isCollapsed && (
              <button
                type="button"
                onClick={() => setAreFoldersExpanded((current) => !current)}
                className="ml-1 rounded p-1.5 text-current hover:bg-primary-text/10"
                title={areFoldersExpanded ? 'Collapse folders' : 'Expand folders'}
                aria-label={areFoldersExpanded ? 'Collapse folders' : 'Expand folders'}
                aria-expanded={areFoldersExpanded}
              >
                {areFoldersExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}
            <button
              type="button"
              onClick={() => selectLessons(null)}
              className={`flex min-w-0 flex-1 items-center rounded-lg ${isCollapsed ? 'justify-center p-3' : 'py-3 pr-3'}`}
              title={isCollapsed ? 'My Lessons' : undefined}
            >
              {isLessonsPath && selectedFolderId === null ? <FolderOpen size={20} /> : <Folder size={20} />}
              {!isCollapsed && <span className="ml-3 truncate text-sm font-medium">My Lessons</span>}
            </button>
            {!isCollapsed && (
              <button type="button" onClick={() => openCreate(null)} className="mr-2 rounded-md p-1.5 text-current hover:bg-primary-text/10" title="Add folder">
                <FolderPlus size={18} />
              </button>
            )}
          </span>

          {!isCollapsed && areFoldersExpanded && (
            <>
              {isLoading && (
                <section className="ml-4 space-y-2 border-l border-border py-2 pl-3" aria-busy="true">
                  <Skeleton className="h-8 w-4/5 rounded-lg" />
                  <Skeleton className="h-8 w-3/5 rounded-lg" />
                  <SkeletonStatus>Loading folders</SkeletonStatus>
                </section>
              )}
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
                collapsedFolderIds={collapsedFolderIds}
                onToggle={toggleFolder}
                activeDropTarget={activeDropTarget}
                onDragEnter={enterDropTarget}
                onDragLeave={leaveDropTarget}
                onDrop={(event, folderId) => void dropIntoFolder(event, folderId)}
              />
            </>
          )}

          <section
            onDragEnter={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setAreLessonSetsExpanded(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              event.stopPropagation();
            }}
            onDrop={(event) => {
              event.preventDefault();
              event.stopPropagation();
              setDropMessage(null);
              setDropError('Drop the lesson on a named lesson set below.');
            }}
            className={`mt-2 flex w-full items-center rounded-lg border transition-colors ${
            isLessonSetsIndexPath
              ? 'border-transparent bg-surface text-primary-text'
              : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          }`}>
            {!isCollapsed && (
              <button
                type="button"
                onClick={() => setAreLessonSetsExpanded((current) => !current)}
                className="ml-1 rounded p-1.5 text-current hover:bg-primary-text/10"
                title={areLessonSetsExpanded ? 'Collapse lesson sets' : 'Expand lesson sets'}
                aria-label={areLessonSetsExpanded ? 'Collapse lesson sets' : 'Expand lesson sets'}
                aria-expanded={areLessonSetsExpanded}
              >
                {areLessonSetsExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}
            <Link
              href="/dashboard/sets"
              className={`flex min-w-0 flex-1 items-center rounded-lg ${isCollapsed ? 'justify-center p-3' : 'py-3 pr-3'}`}
              title={isCollapsed ? 'Lesson Sets' : undefined}
            >
              <LibraryBig size={20} className={isCollapsed ? '' : 'mr-3'} />
              {!isCollapsed && <span className="truncate text-sm font-medium">Lesson Sets</span>}
            </Link>
          </section>

          {!isCollapsed && areLessonSetsExpanded && (
            <ul className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
              {areLessonSetsLoading && (
                <li className="space-y-2 px-3 py-2" aria-busy="true">
                  <Skeleton className="h-7 w-full rounded-md" />
                  <Skeleton className="h-7 w-4/5 rounded-md" />
                  <SkeletonStatus>Loading lesson sets</SkeletonStatus>
                </li>
              )}
              {lessonSetsError && <li className="px-3 py-2 text-xs text-red-300">{lessonSetsError}</li>}
              {!areLessonSetsLoading && lessonSets.length === 0 && (
                <li className="px-3 py-2 text-xs text-secondary-text">No lesson sets yet</li>
              )}
              {lessonSets.map((lessonSet) => {
                const target = `set:${lessonSet.id}`;
                const isActive = pathname === `/dashboard/sets/${lessonSet.id}`;
                return (
                  <li key={lessonSet.id}>
                    <section
                      onDragEnter={(event) => enterDropTarget(event, target, 'copy')}
                      onDragOver={(event) => enterDropTarget(event, target, 'copy')}
                      onDragLeave={(event) => leaveDropTarget(event, target)}
                      onDrop={(event) => void dropIntoLessonSet(event, lessonSet.id)}
                      className={`flex min-h-9 items-center rounded-md border text-sm transition-colors ${
                        activeDropTarget === target
                          ? 'border-accent bg-accent/20 text-primary-text'
                          : isActive
                            ? 'border-transparent bg-surface text-primary-text'
                            : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
                      }`}
                    >
                      <span className="ml-1 size-6 shrink-0" aria-hidden="true" />
                      <Link
                        href={`/dashboard/sets/${lessonSet.id}`}
                        className="flex min-w-0 flex-1 items-center gap-2 px-2 py-2"
                        title={`Open ${lessonSet.title}; drop a lesson to add it`}
                      >
                        <LibraryBig size={15} className="shrink-0" />
                        <span className="min-w-0 flex-1 truncate">{lessonSet.title}</span>
                        <span className="text-xs text-secondary-text">{lessonSet.lesson_count}</span>
                      </Link>
                    </section>
                  </li>
                );
              })}
            </ul>
          )}

          {!isCollapsed && (dropMessage || dropError) && (
            <p
              role="status"
              className={`mx-2 mt-2 rounded-md px-2 py-2 text-xs ${dropError ? 'bg-red-950/40 text-red-300' : 'bg-emerald-950/40 text-emerald-300'}`}
            >
              {dropError ?? dropMessage}
            </p>
          )}
        </section>

        {!isCollapsed && (
          <p className="px-3 pt-3 text-xs font-semibold uppercase tracking-wider text-secondary-text/70">Sharing</p>
        )}
        <Link
          href="/dashboard/published"
          className={`group flex w-full items-center rounded-lg border transition-colors ${
            isPublishedPath ? 'border-transparent bg-surface text-primary-text' : 'border-transparent text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
          } ${isCollapsed ? 'justify-center p-3' : 'px-3 py-3'}`}
          title={isCollapsed ? 'Published Lessons' : undefined}
        >
          <Globe2 size={20} className={isCollapsed ? '' : 'mr-3'} />
          {!isCollapsed && <span className="text-sm font-medium">Published Lessons</span>}
        </Link>
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
