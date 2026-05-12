'use client'

import Link from "next/link";
import { Trash2, EllipsisVertical } from "lucide-react";
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import { TriangleAlert } from "lucide-react";
import React from "react";
import Dropdown from "../ui/Dropdown";

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
    const [isDeleteModalOpen, setIsDeleteModalOpen] = React.useState(false);
    const formatLabels: Record<string, string> = {
        manim: 'Pro Video',
        remotion: 'Instant Video',
        'p5.js': 'Interactive Display',
        'reveal.js': 'Presentation',
    };

    const formattedDate = new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    }).format(new Date(createdAt));
    const formatLabel = formatLabels[format] ?? format;

    const onEllipsisClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        <Dropdown>
            options={models}
            value={value}
            onChange={onChange}
            placeholder="Select a format"
        </Dropdown>
    }

    return (
        <article className="relative min-h-48 rounded-lg border border-border bg-surface p-4 flex flex-col">
            <Link
                href={`/generation?lessonId=${id}`}
                className="absolute inset-0 z-0 rounded-lg"
                title="Open lesson"
            />
            <div className="relative z-10 flex items-start justify-between gap-3">
                <h3 className="min-w-0 text-xl font-semibold text-primary-text leading-snug line-clamp-2">{title}</h3>
                <button 
                    type="button"
                    onClick={onEllipsisClick}
                    className="ml-auto shrink-0 rounded-md p-1 text-secondary-text transition-colors hover:bg-primary-text/10"
                    title="More actions"
                >
                    <EllipsisVertical size={20} />
                </button>
            </div>
            <div className="relative z-10 mt-auto flex items-center justify-between gap-3 pt-4">
                <p className="truncate text-xs text-secondary-text">{formattedDate}</p>
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => setIsDeleteModalOpen(true)}
                        className="rounded-lg p-2 text-secondary-text transition-colors hover:bg-primary-bg hover:text-red-400"
                        title="Delete lesson"
                    >
                        <Trash2 size={18} />
                    </button>
                </div>
            </div>
            {/* Delete Confirmation Modal */}
            <div className="relative z-20">
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
                </div>
        </article>
    );
}
