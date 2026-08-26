'use client';

import { EyeOff, Globe2 } from 'lucide-react';
import { useState } from 'react';

import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';

interface PublishLessonButtonProps {
  authorName: string;
  isPublished: boolean;
  isBusy: boolean;
  disabled?: boolean;
  onPublish: () => Promise<boolean>;
  onUnpublish: () => Promise<boolean>;
}

export default function PublishLessonButton({
  authorName,
  isPublished,
  isBusy,
  disabled = false,
  onPublish,
  onUnpublish,
}: PublishLessonButtonProps) {
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  async function confirmPublish() {
    if (await onPublish()) setIsConfirmOpen(false);
  }

  if (isPublished) {
    return (
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || isBusy}
        onClick={() => void onUnpublish()}
        className="gap-1.5"
      >
        <EyeOff size={14} />
        {isBusy ? 'Unpublishing…' : 'Unpublish'}
      </Button>
    );
  }

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        disabled={disabled || isBusy}
        onClick={() => setIsConfirmOpen(true)}
        className="gap-1.5"
      >
        <Globe2 size={14} />
        Publish
      </Button>
      <Modal
        isOpen={isConfirmOpen}
        onClose={() => !isBusy && setIsConfirmOpen(false)}
        title="Publish this lesson?"
      >
        <p>
          After publishing, everyone can find this lesson in Explore, view it, and download it.
          Other people cannot modify your lesson, and you can unpublish it later at any time.
        </p>
        <p className="mt-3 text-sm">
          It will be published as <span className="font-semibold text-primary-text">{authorName}</span>.
          Your email address will not be shown.
        </p>
        <section className="mt-6 flex w-full gap-3">
          <Button
            variant="secondary"
            className="w-full"
            disabled={isBusy}
            onClick={() => setIsConfirmOpen(false)}
          >
            Cancel
          </Button>
          <Button
            className="w-full"
            disabled={isBusy}
            onClick={() => void confirmPublish()}
          >
            {isBusy ? 'Publishing…' : 'Publish'}
          </Button>
        </section>
      </Modal>
    </>
  );
}
