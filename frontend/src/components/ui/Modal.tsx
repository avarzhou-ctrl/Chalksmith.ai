'use client';

import { useEffect, useId, useRef } from 'react';
import { X } from 'lucide-react';
import type { ReactNode } from 'react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
}

export default function Modal({
    isOpen,
    onClose,
    title,
    children
}: ModalProps) {
    const titleId = useId();
    const dialogRef = useRef<HTMLDivElement>(null);
    const onCloseRef = useRef(onClose);

    useEffect(() => {
        onCloseRef.current = onClose;
    }, [onClose]);

    useEffect(() => {
        if (!isOpen) return;

        const previouslyFocused = document.activeElement as HTMLElement | null;
        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        const frame = window.requestAnimationFrame(() => {
            const autofocusTarget = dialogRef.current?.querySelector<HTMLElement>('[autofocus]');
            (autofocusTarget ?? dialogRef.current)?.focus();
        });
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                event.preventDefault();
                onCloseRef.current();
                return;
            }
            if (event.key !== 'Tab') return;
            const focusable = Array.from(dialogRef.current?.querySelectorAll<HTMLElement>(
                'button:not(:disabled), [href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])',
            ) ?? []);
            if (!focusable.length) {
                event.preventDefault();
                dialogRef.current?.focus();
                return;
            }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.cancelAnimationFrame(frame);
            window.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = previousOverflow;
            previouslyFocused?.focus();
        };
    }, [isOpen]);

  if (!isOpen) return null;

    return (
        <section className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
                aria-hidden="true"
                className="absolute inset-0 cursor-default bg-stone-950/70 backdrop-blur-[2px] transition-opacity"
                onMouseDown={onClose}
            />

            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby={titleId}
                tabIndex={-1}
                className="relative z-10 flex max-h-[calc(100dvh-2rem)] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-border bg-secondary-bg pt-8 shadow-2xl animate-in fade-in zoom-in-95 duration-200"
            >
                <button
                    type="button"
                    onClick={onClose}
                    className="absolute right-4 top-4 rounded-lg p-1.5 text-secondary-text transition-colors hover:bg-surface/50"
                    aria-label="Close dialog"
                >
                    <X size={20} aria-hidden="true" />
                </button>

                <div className="mb-6 shrink-0 px-8 text-center">
                    <h2 id={titleId} className="text-xl font-bold text-primary-text">{title}</h2>
                </div>

                <div className="min-h-0 overflow-y-auto px-8 pb-10 text-center leading-relaxed text-secondary-text">
                    {children}
                </div>
            </div>
        </section>
    );
}
