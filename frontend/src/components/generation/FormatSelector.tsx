'use client';

import Dropdown from '@/components/ui/Dropdown';

interface FormatSelectorProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    isEditMode?: boolean;
}

export default function FormatSelector({ value, onChange, disabled, isEditMode }: FormatSelectorProps) {
    const models = [
        { label: 'Instant Video', value: 'remotion' },
        { label: 'Pro Video', value: 'manim' },
        { label: 'Presentation', value: 'reveal.js' },
        { label: 'Interactive Display', value: 'p5.js' }
    ];
    
    return (
        <div className="flex flex-col gap-1.5 min-w-0">
            <label className="text-xs font-semibold text-secondary-text uppercase tracking-wider truncate whitespace-nowrap">Format</label>
            <Dropdown
                options={models}
                value={value}
                onChange={onChange}
                placeholder="Select a format"
                disabled={disabled || isEditMode}
            />
        </div>
    );
}