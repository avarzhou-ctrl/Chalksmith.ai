'use client';

import Dropdown from '@/components/ui/Dropdown';

interface ModelSelectorProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export default function ModelSelector({ value, onChange, disabled }: ModelSelectorProps) {
    const models = [
        { label: 'Gemini 3.5 Flash', value: 'gemini-3.5-flash' },
        { label: 'Gemini 3.1 Pro', value: 'gemini-3.1-pro-preview' },
        // { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
        // { label: 'GPT-4o', value: 'gpt-4o' },
        // { label: 'DeepSeek Chat', value: 'deepseek-chat' },
        // { label: 'DeepSeek Reasoner', value: 'deepseek-reasoner' }
    ];
    
    return (
        <div className="flex flex-col gap-1.5 min-w-0">
            <label className="text-xs font-semibold text-secondary-text uppercase tracking-wider truncate whitespace-nowrap">AI Model</label>
            <Dropdown
                options={models}
                value={value}
                onChange={onChange}
                placeholder="Select a model"
                disabled={disabled}    
            />
        </div>
    );
}