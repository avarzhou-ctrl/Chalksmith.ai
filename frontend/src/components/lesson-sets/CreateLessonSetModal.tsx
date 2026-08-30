'use client';

import { FormEvent, useEffect, useState } from 'react';

import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

interface CreateLessonSetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (title: string, description: string) => Promise<void>;
}

export default function CreateLessonSetModal({
  isOpen,
  onClose,
  onCreate,
}: CreateLessonSetModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setTitle('');
      setDescription('');
      setError(null);
    }
  }, [isOpen]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    try {
      setIsSaving(true);
      setError(null);
      await onCreate(title.trim(), description.trim());
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to create lesson set.');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create lesson set">
      <form onSubmit={submit} className="text-left">
        <label htmlFor="lesson-set-title" className="text-sm font-medium text-primary-text">Title</label>
        <input
          id="lesson-set-title"
          autoFocus
          maxLength={160}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Grade 6 Fractions Unit"
          className="mt-2 h-11 w-full rounded-lg border border-border bg-primary-bg px-3 text-primary-text outline-none focus:border-accent"
        />
        <label htmlFor="lesson-set-description" className="mt-5 block text-sm font-medium text-primary-text">Description</label>
        <textarea
          id="lesson-set-description"
          maxLength={2000}
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Describe the sequence or teaching goal."
          className="mt-2 w-full resize-none rounded-lg border border-border bg-primary-bg p-3 text-primary-text outline-none focus:border-accent"
        />
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        <span className="mt-6 flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" disabled={isSaving || !title.trim()}>{isSaving ? 'Creating…' : 'Create set'}</Button>
        </span>
      </form>
    </Modal>
  );
}
