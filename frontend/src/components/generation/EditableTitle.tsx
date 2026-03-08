'use client'

import { useState } from "react";

interface EditableTitleProps {
    initialTitle?: string;
    onChange?: (newTitle: string) => void;
}

export default function EditableTitle({ initialTitle = "Untitled", onChange }: EditableTitleProps) {
    const [title, setTitle] = useState(initialTitle);
    const [isEditing, setIsEditing] = useState(false);
    
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

    return (
        <div className="flex flex-row items-center gap-4 group">
            {isEditing ? (
                <input
                    className="text-3xl font-bold bg-secondary-bg text-primary-text border-b-2 border-accent outline-none px-1 rounded transition-colors"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onBlur={handleBlur}
                    onKeyDown={handleKeyDown}
                />
            ) : (
                <h1 className="text-3xl font-bold bg-secondary-bg text-primary-text border-b-2 border-accent outline-none px-1 rounded transition-colors" onDoubleClick={() => setIsEditing(true)}>
                    {title}
                </h1>
            )}
        </div>
    );
}
