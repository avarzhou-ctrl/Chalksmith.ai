'use client';

import { Folder, FolderOpen } from 'lucide-react';

import type { LessonFolder } from '@/lib/types/api';

interface FolderPickerProps {
  folders: LessonFolder[];
  value: string | null;
  onChange: (folderId: string | null) => void;
  disabled?: boolean;
}

function FolderOptions({
  folders,
  parentId,
  value,
  onChange,
  disabled,
}: FolderPickerProps & { parentId: string | null }) {
  const children = folders
    .filter((folder) => folder.parent_id === parentId)
    .sort((left, right) => left.name.localeCompare(right.name));

  if (!children.length) return null;

  return (
    <ul className={parentId ? 'ml-4 border-l border-border pl-2' : ''}>
      {children.map((folder) => (
        <li key={folder.id}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onChange(folder.id)}
            className={`flex min-h-10 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors disabled:opacity-50 ${
              value === folder.id
                ? 'bg-accent text-primary-text'
                : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
            }`}
          >
            {value === folder.id ? <FolderOpen size={16} /> : <Folder size={16} />}
            <span className="truncate">{folder.name}</span>
          </button>
          <FolderOptions
            folders={folders}
            parentId={folder.id}
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        </li>
      ))}
    </ul>
  );
}

export default function FolderPicker({ folders, value, onChange, disabled = false }: FolderPickerProps) {
  return (
    <section className="max-h-72 overflow-y-auto text-left [scrollbar-color:var(--color-border)_transparent] [scrollbar-width:thin] [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-stone-600 [&::-webkit-scrollbar-thumb:hover]:bg-stone-500 [&::-webkit-scrollbar-track]:bg-transparent">
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(null)}
        className={`flex min-h-10 w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors disabled:opacity-50 ${
          value === null
            ? 'bg-accent text-primary-text'
            : 'text-secondary-text hover:bg-primary-text/10 hover:text-primary-text'
        }`}
      >
        {value === null ? <FolderOpen size={16} /> : <Folder size={16} />}
        <span>Lessons</span>
      </button>
      <FolderOptions
        folders={folders}
        parentId={null}
        value={value}
        onChange={onChange}
        disabled={disabled}
      />
    </section>
  );
}
