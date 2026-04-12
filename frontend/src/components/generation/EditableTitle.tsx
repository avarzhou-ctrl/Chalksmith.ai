'use client'

import { useState, useEffect } from "react";

interface EditableTitleProps {
    initialTitle?: string;
    onChange?: (newTitle: string) => void;
}

export default function EditableTitle({ initialTitle = "Untitled", onChange }: EditableTitleProps) {
    const [title, setTitle] = useState(initialTitle);
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        setTitle(initialTitle);
    }, [initialTitle]);
    
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            setIsEditing(false);
            if (onChange) onChange(title);
        }
        if (e.key === 'Escape') {
            setIsEditing(false);
            setTitle(initialTitle);
        }
    };

    const handleBlur = () => {
        setIsEditing(false);
        if (onChange) onChange(title);
    };

    // Shared styles for alignment and zero layout shift
    const sharedStyles = "text-3xl font-bold px-3 py-1 rounded-lg border transition-all duration-200 w-full";

    return (
        <div className="flex flex-row items-center gap-4 group min-w-0 flex-1">
            {isEditing ? (
                <input
                    className={`bg-secondary-bg text-primary-text border-accent ring-1 ring-accent/20 outline-none shadow-lg shadow-accent/5 ${sharedStyles}`}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onBlur={handleBlur}
                    onKeyDown={handleKeyDown}
                    autoFocus
                />
            ) : (
                <h1 
                    className={`bg-transparent text-primary-text border-transparent hover:border-accent/30 hover:bg-surface/30 cursor-pointer truncate ${sharedStyles}`} 
                    onDoubleClick={() => setIsEditing(true)}
                    title={title}
                >
                    {title}
                </h1>
            )}
        </div>
    );
}
