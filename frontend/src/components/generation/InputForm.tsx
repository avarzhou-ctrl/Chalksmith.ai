'use client'

import FormatSelector from './FormatSelector';
import Textarea from '@/components/ui/Textarea';
import { CircleArrowUp, CirclePause } from 'lucide-react';
import type { LessonFormat } from '@/lib/types/api';

const TOPIC_CHARACTER_LIMIT = 200;

interface InputFormProps {
    format: LessonFormat | '';
    topic: string;
    onFormatChange: (value: LessonFormat) => void;
    onTopicChange: (value: string) => void;
    onGenerate: () => void;
    onStopGenerate: () => void;
    sourceFiles: File[];
    onSourceFilesChange: (files: File[]) => void;
    disabled?: boolean;
    isEditMode?: boolean;
}

export default function InputForm({ 
    format, 
    topic, 
    onFormatChange, 
    onTopicChange, 
    onGenerate,
    onStopGenerate,
    sourceFiles,
    onSourceFilesChange,
    disabled,
    isEditMode
}: InputFormProps) {
    const canGenerate = Boolean(format && (topic.trim() || sourceFiles.length));
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
                    disabled={!canGenerate}
                    className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors disabled:opacity-40"
                >
                    <CircleArrowUp size={20} />
                </button>
            )}
        </div>
    );

    return (
        <div className="flex flex-col w-full min-w-0 flex-1 min-h-0">
            <div className="flex flex-row gap-4 min-w-0 shrink-0">
                <div className="flex-1 min-w-0">
                    <FormatSelector value={format} onChange={onFormatChange} disabled={disabled || isEditMode} />
                </div>
            </div>
            <div className="relative mt-4 group flex-1 min-h-0 flex flex-col">
                <Textarea 
                    placeholder={isEditMode ? "How should I edit this lesson?" : "Describe your topic..."}
                    disabled={disabled}
                    fileUploadDisabled={disabled}
                    value={topic}
                    maxLength={TOPIC_CHARACTER_LIMIT}
                    files={sourceFiles}
                    onFilesChange={onSourceFilesChange}
                    onChange={(e) => onTopicChange(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey && canGenerate && !disabled) {
                            e.preventDefault();
                            onGenerate();
                        }
                    }}
                    className="flex-1 resize-none"
                    containerClassName="h-full min-h-0"
                    generationButton={generationButton}
                />
            </div>
        </div>
    );
}
