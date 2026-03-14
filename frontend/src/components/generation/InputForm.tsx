'use client'

import FormatSelector from './FormatSelector';
import ModelSelector from './ModelSelector';
import Textarea from '@/components/ui/Textarea';

interface InputFormProps {
    model: string;
    format: string;
    topic: string;
    onModelChange: (value: string) => void;
    onFormatChange: (value: string) => void;
    onTopicChange: (value: string) => void;
    disabled?: boolean;
}

export default function InputForm({ 
    model, 
    format, 
    topic, 
    onModelChange, 
    onFormatChange, 
    onTopicChange, 
    disabled 
}: InputFormProps) {
    return (
        <div className="flex flex-col gap-6 w-full min-w-0">
            <div className="flex flex-row gap-4 min-w-0">
                <div className="flex-1 min-w-0">
                    <ModelSelector value={model} onChange={onModelChange} disabled={disabled} />
                </div>
                <div className="flex-1 min-w-0">
                    <FormatSelector value={format} onChange={onFormatChange} disabled={disabled} />
                </div>
            </div>
            <Textarea 
                className="mt-4"
                placeholder="Describe your topic..."
                disabled={disabled}
                value={topic}
                onChange={(e) => onTopicChange(e.target.value)}
            />
        </div>
    );
}