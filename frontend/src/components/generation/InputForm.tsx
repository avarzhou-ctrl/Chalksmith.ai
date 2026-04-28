'use client'

import { GenerationStatus } from '@/lib/api';
import FormatSelector from './FormatSelector';
import ModelSelector from './ModelSelector';
import Textarea from '@/components/ui/Textarea';
import { CircleArrowUp, CirclePause } from 'lucide-react';

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
    return (
        <div className="flex flex-col w-full min-w-0">
            <div className="flex flex-row gap-4 min-w-0">
                <div className="flex-1 min-w-0">
                    <ModelSelector value={model} onChange={onModelChange} disabled={disabled} />
                </div>
                <div className="flex-1 min-w-0">
                    {/* Disabling format change in Edit Mode as changing formats mid-conversation is unsupported */}
                    <FormatSelector value={format} onChange={onFormatChange} disabled={disabled || isEditMode} />
                </div>
            </div>
            <div className="relative mt-4 group">
                <Textarea 
                    placeholder={isEditMode ? "How should I edit this lesson?" : "Describe your topic..."}
                    disabled={disabled}
                    value={topic}
                    onChange={(e) => onTopicChange(e.target.value)}
                    onKeyDown={(e) => {
                        // Standard chat UX: Enter sends, Shift+Enter adds a new line
                        if (e.key === 'Enter' && !e.shiftKey && topic.trim() && !disabled) {
                            e.preventDefault();
                            onGenerate();
                        }
                    }}
                    className="pr-12 h-24"
                />

                <div className="absolute bottom-2 right-2">
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
                            disabled={!topic.trim()}
                            className="p-1.5 hover:bg-surface/50 rounded-lg text-accent transition-colors disabled:opacity-40"
                        >
                            <CircleArrowUp size={20} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
