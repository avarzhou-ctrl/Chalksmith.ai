'use client';

import Dropdown from '@/components/ui/Dropdown';
import { LESSON_FORMAT_OPTIONS, type LessonFormat } from '@/lib/types/api';

interface FormatSelectorProps {
    value: LessonFormat | '';
    onChange: (value: LessonFormat) => void;
    disabled?: boolean;
}

export default function FormatSelector({ value, onChange, disabled }: FormatSelectorProps) {
    return (
        <div className="flex flex-col gap-1.5 min-w-0">
            <label className="text-xs font-semibold text-secondary-text uppercase tracking-wider truncate whitespace-nowrap">Format</label>
            <Dropdown
                options={LESSON_FORMAT_OPTIONS}
                value={value}
                onChange={(nextValue) => onChange(nextValue as LessonFormat)}
                placeholder="Select a format"
                disabled={disabled}
            />
        </div>
    );
}
