'use client'

import { GenerationStatus } from '@/lib/api';
import FormatSelector from './FormatSelector';
import Textarea from '@/components/ui/TextArea';
import { CircleArrowUp, CirclePause } from 'lucide-react';
import { useState } from 'react';

const TOPIC_CHARACTER_LIMIT = 100;

interface InputFormProps {
    model: string;
    format: string;
    topic: string;
    onModelChange: (value: string) => void;
    onFormatChange: (value: string) => void;
    onTopicChange: (value: string) => void;
    onGenerate: () => void;
    onStopGenerate: () => void;
    disabled?: boolean;
    isEditMode?: boolean;
    generationStatus: GenerationStatus | null;
}

export default function InputForm({ 
    model, 
    format, 
    topic, 
    onModelChange, 
    onFormatChange, 
    onTopicChange, 
    onGenerate,
    onStopGenerate,
    disabled,
    isEditMode,
    generationStatus
}: InputFormProps) {
    const [files, setFiles] = useState<File[]>([]);

    const handleFileDrop = (newFiles: File[]) => {
        setFiles(prevFiles => [...prevFiles, ...newFiles]);
        console.log("Files dropped: ", newFiles);
    };

    const generationButton = (
        <div>
            {disabled ? (
                <button
                    type="button"
                    title="Stop Generation"
                    onClick={() => onStopGenerate()}
                    className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors"
                >
                    <CirclePause size={20} />
                </button>
            ) : (
                <button
                    type="button"
                    title="Start Generation"
                    onClick={() => onGenerate()}
                    disabled={!topic.trim() || !format}
                    className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors disabled:opacity-40"
                >
                    <CircleArrowUp size={20} />
                </button>
            )}
        </div>
    );

    return (
        <div className="flex flex-col w-full min-w-0 flex-1">
            <div className="flex flex-row gap-4 min-w-0">
                <div className="flex-1 min-w-0">
                    <FormatSelector value={format} onChange={onFormatChange} disabled={disabled || isEditMode} />
                </div>
            </div>
            <div className="relative mt-4 group flex-1 flex flex-col">
                <Textarea 
                    topic={topic}
                    format={format}
                    placeholder={isEditMode ? "How should I edit this lesson?" : "Describe your topic..."}
                    disabled={disabled}
                    value={topic}
                    maxLength={TOPIC_CHARACTER_LIMIT}
                    onChange={(e) => onTopicChange(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey && topic.trim() && !disabled) {
                            e.preventDefault();
                            onGenerate();
                        }
                    }}
                    onFileDrop={handleFileDrop}
                    className="flex-1 resize-none"
                    generationButton={generationButton}
                />
            </div>
        </div>
    );
}

