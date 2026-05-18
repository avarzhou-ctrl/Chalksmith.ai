'use client'

import Link from "next/link";
import { PencilLine, EllipsisVertical, Trash2 } from "lucide-react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import { TriangleAlert } from "lucide-react";
import React from "react";
import EditableTitle from "@/components/generation/EditableTitle";
import { renameLesson } from "@/lib/api";

interface LessonCardProps {
    id: string;
    title: string;
    description: string;
    format: string;
    model: string;
    createdAt: string;
    onDelete: () => void;
}

export default function LessonCard({
    id,
    title,
    description,
    format,
    model,
    createdAt,
    onDelete,
}: LessonCardProps) {
    const [displayTitle, setDisplayTitle] = React.useState(title);
    const [renameError, setRenameError] = React.useState<string | null>(null);
    const [isRenaming, setIsRenaming] = React.useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = React.useState(false);
    const [isActionsOpen, setIsActionsOpen] = React.useState(false);
    const actionsRef = React.useRef<HTMLDivElement>(null);
    const formatLabels: Record<string, string> = {
        manim: 'Pro Video',
        remotion: 'Instant Video',
        'p5.js': 'Interactive Display',
        'reveal.js': 'Presentation',
    };
    
    const [isRenameModalOpen, setIsRenameModalOpen] = React.useState(false);

    React.useEffect(() => {
        setDisplayTitle(title);
    }, [title]);

    const formattedDate = new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    }).format(new Date(createdAt));
    const formatLabel = formatLabels[format] ?? format;

    React.useEffect(() => {
        const closeActions = (event: MouseEvent) => {
            if (actionsRef.current && !actionsRef.current.contains(event.target as Node)) {
                setIsActionsOpen(false);
            }
        };

        const closeOnEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setIsActionsOpen(false);
            }
        };

        document.addEventListener('mousedown', closeActions);
        document.addEventListener('keydown', closeOnEscape);

        return () => {
            document.removeEventListener('mousedown', closeActions);
            document.removeEventListener('keydown', closeOnEscape);
        };
    }, []);

    const openDeleteModal = () => {
        setIsActionsOpen(false);
        setIsDeleteModalOpen(true);
    };

    const openRenameModal = () => {
        setIsActionsOpen(false);
        setRenameError(null);
        setIsRenameModalOpen(true);
    };

    const handleRenameLesson = async (newTitle: string) => {
        const trimmedTitle = newTitle.trim();

        if (!trimmedTitle || trimmedTitle === displayTitle) {
            return;
        }

        try {
            setRenameError(null);
            setIsRenaming(true);
            await renameLesson(id, trimmedTitle);
            setDisplayTitle(trimmedTitle);
        } catch (error) {
            setRenameError(error instanceof Error ? error.message : 'Failed to rename lesson');
        } finally {
            setIsRenaming(false);
        }
    };

    return (
        <article className="relative min-h-48 rounded-lg border border-border bg-surface p-4 flex flex-col">
            <Link
                href={`/generation?lessonId=${id}`}
                className="absolute inset-0 z-0 rounded-lg"
                title="Open lesson"
            />
            <div className="relative z-30 flex items-start justify-between gap-3">
                <h3 className="min-w-0 text-xl font-semibold text-primary-text leading-snug line-clamp-2">{displayTitle}</h3>
                <div className="relative ml-auto shrink-0" ref={actionsRef}>
                    <button 
                        type="button"
                        onClick={() => setIsActionsOpen((current) => !current)}
                        className="rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10 focus:outline-none focus:ring-2"
                        title="More actions"
                        aria-haspopup="menu"
                        aria-expanded={isActionsOpen}
                    >
                        <EllipsisVertical size={20} />
                    </button>

                    {isActionsOpen && (
                        <div
                            role="menu"
                            className="absolute right-0 top-8 z-30 w-44 overflow-hidden rounded-lg border border-border bg-secondary-bg p-1 shadow-lg shadow-stone-950 sm:w-48"
                        >
                            <button
                                type="button"
                                role="menuitem"
                                onClick={openRenameModal}
                                className="flex min-h-10 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-primary-text transition-colors hover:bg-primary-text/10 focus:outline-none focus:ring-2"
                            >
                                <PencilLine size={16} />
                                <span className="truncate">Rename</span>
                            </button>
                            <button
                                type="button"
                                role="menuitem"
                                onClick={openDeleteModal}
                                className="flex min-h-10 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-primary-text transition-colors hover:bg-primary-text/10 focus:outline-none focus:ring-2"
                            >
                                <Trash2 size={16} />
                                <span className="truncate">Delete</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
            {description && (
                <p className="relative z-10 mt-3 line-clamp-2 text-sm leading-6 text-secondary-text">{description}</p>
            )}
            <div className="relative z-10 mt-auto flex items-center justify-between gap-3 pt-4">
                <p className="truncate text-xs text-secondary-text">{formattedDate}</p>
                <p className="truncate text-xs text-secondary-text">{formatLabel} | {model}</p>
            </div>
            
            {/* Delete Confirmation Modal */}
            <Modal 
                isOpen={isDeleteModalOpen} 
                onClose={() => setIsDeleteModalOpen(false)} 
                title="Delete lesson?"
            >
                <div className="flex flex-col items-center">
                    <div className="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center mb-4">
                        <TriangleAlert className="text-accent" size={24} />
                    </div>
                    <p className="mb-6 text-center">
                        This will delete your current lesson and chat history. You cannot undo this action.
                    </p>
                    <div className="flex flex-row gap-3 w-full">
                        <Button 
                            variant="secondary" 
                            className="w-full" 
                            onClick={() => setIsDeleteModalOpen(false)}
                        >
                            Close
                        </Button>
                        <Button 
                            variant="primary" 
                            className="w-full bg-accent hover:bg-amber-700 border-none" 
                            onClick={() => {
                                onDelete();
                                setIsDeleteModalOpen(false);
                            }}
                        >
                            Delete
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* Rename Confirmation Modal */}
            <Modal
                isOpen={isRenameModalOpen}
                onClose={() => setIsRenameModalOpen(false)}
                title="Rename lesson?"
            >
                <div className="flex flex-col items-center">
                    <EditableTitle
                        initialTitle={displayTitle}
                        onChange={handleRenameLesson}
                    />
                    {renameError && (
                        <p className="mt-3 text-sm text-red-300">{renameError}</p>
                    )}
                    <div className="mb-3 mt-6 flex w-full flex-row gap-3">
                        <Button 
                            variant="primary" 
                            className="w-full" 
                            disabled={isRenaming}
                            onClick={() => setIsRenameModalOpen(false)}
                        >
                            {isRenaming ? 'Saving...' : 'Close'}
                        </Button>
                    </div>
                </div>
            </Modal>
        </article>
    );
}
