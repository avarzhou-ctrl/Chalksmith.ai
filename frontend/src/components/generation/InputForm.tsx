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
        <div className="flex flex-col gap-6">
            <div className="flex flex-row md:flex-row gap-4">
                <ModelSelector value={model} onChange={onModelChange} disabled={disabled} />
                <FormatSelector value={format} onChange={onFormatChange} disabled={disabled} />
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