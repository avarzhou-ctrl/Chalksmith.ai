'use client';

import { EllipsisVertical, type LucideIcon } from 'lucide-react';
import { useCallback, useEffect, useId, useRef, useState } from 'react';

export interface ActionMenuItem {
  label: string;
  icon: LucideIcon;
  onSelect: () => void;
  disabled?: boolean;
}

interface ActionMenuProps {
  label: string;
  items: ActionMenuItem[];
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export default function ActionMenu({
  label,
  items,
  open,
  onOpenChange,
}: ActionMenuProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const menuId = useId();
  const containerRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLElement>(null);
  const isOpen = open ?? internalOpen;

  const setOpen = useCallback((nextOpen: boolean) => {
    if (open === undefined) setInternalOpen(nextOpen);
    onOpenChange?.(nextOpen);
  }, [onOpenChange, open]);

  useEffect(() => {
    if (!isOpen) return;

    const frame = window.requestAnimationFrame(() => {
      menuRef.current?.querySelector<HTMLButtonElement>('[role="menuitem"]:not(:disabled)')?.focus();
    });
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    };

    document.addEventListener('mousedown', closeOnOutsideClick);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      window.cancelAnimationFrame(frame);
      document.removeEventListener('mousedown', closeOnOutsideClick);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isOpen, setOpen]);

  function moveFocus(event: React.KeyboardEvent<HTMLElement>) {
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    const buttons = Array.from(
      menuRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]:not(:disabled)') ?? [],
    );
    if (!buttons.length) return;
    event.preventDefault();
    const currentIndex = buttons.indexOf(document.activeElement as HTMLButtonElement);
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? buttons.length - 1
        : event.key === 'ArrowUp'
          ? (currentIndex - 1 + buttons.length) % buttons.length
          : (currentIndex + 1) % buttons.length;
    buttons[nextIndex]?.focus();
  }

  return (
    <section ref={containerRef} className="relative">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(!isOpen)}
        className="rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10 focus:outline-none focus:ring-2"
        title={label}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls={isOpen ? menuId : undefined}
      >
        <EllipsisVertical size={20} aria-hidden="true" />
      </button>

      {isOpen && (
        <section
          ref={menuRef}
          id={menuId}
          role="menu"
          onKeyDown={moveFocus}
          className="absolute right-0 top-8 z-30 w-48 overflow-hidden rounded-lg border border-border bg-secondary-bg p-1 shadow-xl shadow-stone-950"
        >
          {items.map(({ label: itemLabel, icon: Icon, onSelect, disabled }) => (
            <button
              key={itemLabel}
              type="button"
              role="menuitem"
              disabled={disabled}
              onClick={() => {
                setOpen(false);
                triggerRef.current?.focus();
                onSelect();
              }}
              className="flex min-h-10 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-primary-text transition-colors hover:bg-primary-text/10 focus:outline-none focus:ring-2 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Icon size={16} aria-hidden="true" />
              <span className="truncate">{itemLabel}</span>
            </button>
          ))}
        </section>
      )}
    </section>
  );
}
