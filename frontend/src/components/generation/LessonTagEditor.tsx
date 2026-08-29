'use client';

import { Tags, X } from 'lucide-react';
import { KeyboardEvent, useEffect, useState } from 'react';

import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

const MAX_TAGS = 5;
const MAX_TAG_LENGTH = 32;

interface LessonTagEditorProps {
  tags: string[];
  isBusy: boolean;
  disabled?: boolean;
  onSave: (tags: string[]) => Promise<boolean>;
}

export default function LessonTagEditor({
  tags,
  isBusy,
  disabled = false,
  onSave,
}: LessonTagEditorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [draftTags, setDraftTags] = useState(tags);
  const [input, setInput] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => setDraftTags(tags), [tags]);

  function openEditor() {
    setDraftTags(tags);
    setInput('');
    setValidationError(null);
    setIsOpen(true);
  }

  function addTag() {
    const label = input.trim().replace(/\s+/g, ' ');
    if (!label) return;
    if (label.length > MAX_TAG_LENGTH) {
      setValidationError(`Tags must be ${MAX_TAG_LENGTH} characters or fewer.`);
      return;
    }
    if (draftTags.some((tag) => tag.toLocaleLowerCase() === label.toLocaleLowerCase())) {
      setInput('');
      setValidationError(null);
      return;
    }
    if (draftTags.length >= MAX_TAGS) {
      setValidationError(`Lessons can have at most ${MAX_TAGS} tags.`);
      return;
    }
    setDraftTags((current) => [...current, label]);
    setInput('');
    setValidationError(null);
  }

  function handleInputKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      addTag();
    }
  }

  async function saveTags() {
    const pending = input.trim().replace(/\s+/g, ' ');
    let tagsToSave = draftTags;
    if (pending && !draftTags.some((tag) => tag.toLocaleLowerCase() === pending.toLocaleLowerCase())) {
      if (pending.length > MAX_TAG_LENGTH) {
        setValidationError(`Tags must be ${MAX_TAG_LENGTH} characters or fewer.`);
        return;
      }
      if (draftTags.length >= MAX_TAGS) {
        setValidationError(`Lessons can have at most ${MAX_TAGS} tags.`);
        return;
      }
      tagsToSave = [...draftTags, pending];
    }
    if (await onSave(tagsToSave)) setIsOpen(false);
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || isBusy}
        onClick={openEditor}
        className="gap-1.5"
      >
        <Tags size={14} />
        Tags{tags.length ? ` (${tags.length})` : ''}
      </Button>
      <Modal
        isOpen={isOpen}
        onClose={() => !isBusy && setIsOpen(false)}
        title="Lesson tags"
      >
        <p className="text-sm text-secondary-text">
          Add up to five tags to organize this lesson and help people find it in Explore.
        </p>
        <section className="mt-4 flex min-h-11 flex-wrap items-center gap-2 rounded-lg border border-border bg-primary-bg p-2 focus-within:border-accent">
          {draftTags.map((tag) => (
            <span key={tag.toLocaleLowerCase()} className="flex items-center gap-1 rounded-full bg-accent/15 px-3 py-1 text-sm text-accent">
              {tag}
              <button
                type="button"
                onClick={() => setDraftTags((current) => current.filter((value) => value !== tag))}
                className="rounded-full p-0.5 hover:bg-accent/15 focus:outline-none focus:ring-2"
                aria-label={`Remove ${tag}`}
              >
                <X size={13} />
              </button>
            </span>
          ))}
          {draftTags.length < MAX_TAGS && (
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleInputKeyDown}
              onBlur={addTag}
              maxLength={MAX_TAG_LENGTH + 1}
              placeholder={draftTags.length ? 'Add another tag' : 'e.g. Math, Fractions'}
              className="h-8 min-w-40 flex-1 bg-transparent px-1 text-sm text-primary-text outline-none placeholder:text-secondary-text"
            />
          )}
        </section>
        <p className="mt-2 text-xs text-secondary-text">Press Enter or comma to add a tag.</p>
        {validationError && <p className="mt-3 text-sm text-red-300">{validationError}</p>}
        <section className="mt-6 flex gap-3">
          <Button variant="secondary" className="flex-1" disabled={isBusy} onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button className="flex-1" disabled={isBusy} onClick={() => void saveTags()}>
            {isBusy ? 'Saving…' : 'Save tags'}
          </Button>
        </section>
      </Modal>
    </>
  );
}
