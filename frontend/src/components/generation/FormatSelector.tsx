'use client';

import Dropdown from '@/components/ui/Dropdown';

interface FormatSelectorProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export default function FormatSelector({ value, onChange, disabled }: FormatSelectorProps) {
    const models = [
        { label: 'Interactive Display', value: 'interactive' },
        { label: 'Presentation', value: 'slides' },
        { label: 'Video', value: 'video' }
    ];
    
    return (
        <div className="flex flex-col gap-1.5 min-w-0">
            <label className="text-xs font-semibold text-secondary-text uppercase tracking-wider truncate whitespace-nowrap">Format</label>
            <Dropdown
                options={models}
                value={value}
                onChange={onChange}
                placeholder="Select a format"
                disabled={disabled}
            />
        </div>
    );
}
