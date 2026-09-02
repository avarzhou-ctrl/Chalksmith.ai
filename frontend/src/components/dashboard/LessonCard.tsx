'use client'

import Link from "next/link";
import { BookPlus, FolderInput, Globe2, LibraryBig, PencilLine, Trash2 } from "lucide-react";
import LessonCardLayout from '@/components/lesson/LessonCardLayout';
import FolderPicker from '@/components/dashboard/FolderPicker';
import AddToLessonSetModal from '@/components/lesson-sets/AddToLessonSetModal';
import Modal from "@/components/ui/Modal";
import Button from "@/components/ui/Button";
import ActionMenu, { type ActionMenuItem } from '@/components/ui/ActionMenu';
import { TriangleAlert } from "lucide-react";
import EditableTitle from '@/components/lesson/EditableTitle';
import { renameLesson } from "@/lib/api/lessons";
import { useApi } from "@/lib/hooks/useApi";
import {
    dispatchLessonAddedToSet,
    LESSON_ADDED_TO_SET_EVENT,
    setLessonDragData,
    type LessonAddedToSetDetail,
} from '@/lib/lesson-drag';
import { type LessonFolder, type LessonFormat, type LessonListItem } from '@/lib/types/api';
import { useState, useEffect } from "react";

interface LessonCardProps {
    id: string;
    title: string;
    description: React.ReactNode;
    format: LessonFormat;
    status: LessonListItem['status'];
    isPublished: boolean;
    tags: string[];
    createdAt: string;
    versionCount: number;
    lessonSetCount: number;
    folderId: string | null;
    folders: LessonFolder[];
    onDelete: () => void;
    onMove: (folderId: string | null) => Promise<void>;
}

export default function LessonCard({
    id,
    title,
    description,
    format,
    status,
    isPublished,
    tags,
    createdAt,
    versionCount,
    lessonSetCount,
    folderId,
    folders,
    onDelete,
    onMove,
}: LessonCardProps) {
    const api = useApi();
    const [displayTitle, setDisplayTitle] = useState(title);
    const [renameError, setRenameError] = useState<string | null>(null);
    const [isRenaming, setIsRenaming] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isActionsOpen, setIsActionsOpen] = useState(false);
    const [isRenameModalOpen, setIsRenameModalOpen] = useState(false);
    const [isMoveModalOpen, setIsMoveModalOpen] = useState(false);
    const [isAddToSetModalOpen, setIsAddToSetModalOpen] = useState(false);
    const [isMoving, setIsMoving] = useState(false);
    const [displayLessonSetCount, setDisplayLessonSetCount] = useState(lessonSetCount);
    const [moveError, setMoveError] = useState<string | null>(null);

    useEffect(() => {
        setDisplayTitle(title);
    }, [title]);

    useEffect(() => {
        setDisplayLessonSetCount(lessonSetCount);
    }, [lessonSetCount]);

    const formattedDate = new Intl.DateTimeFormat(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    }).format(new Date(createdAt));
    const folderPath = (() => {
        const byId = new Map(folders.map((folder) => [folder.id, folder]));
        const names: string[] = [];
        const visited = new Set<string>();
        let currentId = folderId;
        while (currentId && !visited.has(currentId)) {
            visited.add(currentId);
            const folder = byId.get(currentId);
            if (!folder) break;
            names.unshift(folder.name);
            currentId = folder.parent_id;
        }
        return names.join(' / ');
    })();

    useEffect(() => {
        const recordSetAdd = (event: Event) => {
            const detail = (event as CustomEvent<LessonAddedToSetDetail>).detail;
            if (detail.lessonId === id) {
                setDisplayLessonSetCount((current) => current + 1);
            }
        };
        window.addEventListener(LESSON_ADDED_TO_SET_EVENT, recordSetAdd);
        return () => window.removeEventListener(LESSON_ADDED_TO_SET_EVENT, recordSetAdd);
    }, [id]);

    const openDeleteModal = () => {
        setIsDeleteModalOpen(true);
    };

    const openRenameModal = () => {
        setRenameError(null);
        setIsRenameModalOpen(true);
    };

    const openMoveModal = () => {
        setMoveError(null);
        setIsMoveModalOpen(true);
    };

    const openAddToSetModal = () => {
        setIsAddToSetModalOpen(true);
    };

    const handleMoveLesson = async (targetFolderId: string | null) => {
        if (targetFolderId === folderId) {
            setIsMoveModalOpen(false);
            return;
        }
        try {
            setIsMoving(true);
            setMoveError(null);
            await onMove(targetFolderId);
            setIsMoveModalOpen(false);
        } catch (error) {
            setMoveError(error instanceof Error ? error.message : 'Failed to move lesson');
        } finally {
            setIsMoving(false);
        }
    };

    const handleRenameLesson = async (newTitle: string) => {
        const trimmedTitle = newTitle.trim();

        if (!trimmedTitle || trimmedTitle === displayTitle) {
            return;
        }

        try {
            setRenameError(null);
            setIsRenaming(true);
            await renameLesson(api, id, trimmedTitle);
            setDisplayTitle(trimmedTitle);
        } catch (error) {
            setRenameError(error instanceof Error ? error.message : 'Failed to rename lesson');
        } finally {
            setIsRenaming(false);
        }
    };

    const actionItems: ActionMenuItem[] = [
        ...(status !== 'deleting' ? [
            { label: 'Rename', icon: PencilLine, onSelect: openRenameModal },
            { label: 'Move to folder', icon: FolderInput, onSelect: openMoveModal },
        ] : []),
        ...(status === 'ready' ? [
            { label: 'Add to lesson set', icon: BookPlus, onSelect: openAddToSetModal },
        ] : []),
        { label: status === 'deleting' ? 'Retry delete' : 'Delete', icon: Trash2, onSelect: openDeleteModal },
    ];

    return (
        <LessonCardLayout
            format={format}
            title={displayTitle}
            subtitle={`Created ${formattedDate}${folderPath ? ` · ${folderPath}` : ''}`}
            description={description}
            tags={tags}
            draggable={status === 'ready'}
            onDragStart={(event) => {
                setIsActionsOpen(false);
                setLessonDragData(event.dataTransfer, { lessonId: id, title: displayTitle });
                event.currentTarget.classList.add('opacity-60');
            }}
            onDragEnd={(event) => event.currentTarget.classList.remove('opacity-60')}
            overlay={status !== 'deleting' ? (
                <Link
                    href={`/generation?lessonId=${id}`}
                    className="absolute inset-0 z-0 rounded-2xl"
                    title="Open lesson"
                />
            ) : undefined}
            headerAction={(
                <ActionMenu
                    label="More actions"
                    items={actionItems}
                    open={isActionsOpen}
                    onOpenChange={setIsActionsOpen}
                />
            )}
            statusMessage={status !== 'ready' ? (
                <p className="text-xs font-medium text-amber-400">
                    {status === 'deleting' ? 'Deletion pending—retry from the menu.' : `Status: ${status}`}
                </p>
            ) : undefined}
            footer={(
                <div className="flex min-h-8 items-center justify-between gap-3">
                    <section className="flex min-w-0 items-center gap-2">
                    {isPublished && (
                        <span
                            title="Published to Explore"
                            aria-label="Published to Explore"
                            className="inline-flex min-h-8 items-center gap-1.5 rounded-lg border border-accent/30 bg-accent/10 px-2.5 py-1.5 text-xs font-medium text-accent"
                        >
                            <Globe2 size={14} aria-hidden="true" />
                            Published
                        </span>
                    )}
                    {displayLessonSetCount > 0 && (
                        <span
                            title={`Included in ${displayLessonSetCount} ${displayLessonSetCount === 1 ? 'lesson set' : 'lesson sets'}`}
                            className="inline-flex min-h-8 items-center gap-1.5 rounded-lg border border-accent/30 bg-accent/10 px-2.5 py-1.5 text-xs font-medium text-accent"
                        >
                            <LibraryBig size={14} aria-hidden="true" />
                            In {displayLessonSetCount} {displayLessonSetCount === 1 ? 'set' : 'sets'}
                        </span>
                    )}
                    </section>
                    <p className="truncate text-xs text-secondary-text">{versionCount} {versionCount === 1 ? 'version' : 'versions'}</p>
                </div>
            )}
        >
            
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

            <Modal
                isOpen={isMoveModalOpen}
                onClose={() => setIsMoveModalOpen(false)}
                title="Move lesson"
            >
                <FolderPicker
                    folders={folders}
                    value={folderId}
                    onChange={(targetFolderId) => void handleMoveLesson(targetFolderId)}
                    disabled={isMoving}
                />
                {moveError && <p className="mt-3 text-sm text-red-300">{moveError}</p>}
            </Modal>

            <AddToLessonSetModal
                isOpen={isAddToSetModalOpen}
                lessonId={id}
                onClose={() => setIsAddToSetModalOpen(false)}
                onAdded={(lessonSetId) => dispatchLessonAddedToSet({ lessonId: id, lessonSetId })}
            />
        </LessonCardLayout>
    );
}
