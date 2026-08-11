'use client';

import { useEffect, useRef, useState } from 'react';

interface SearchFilterProps {
    format: string;
    onFormatChange: (value: string) => void;
}

const formatOptions = [
    { label: "All formats", value: "" },
    { label: "Interactive Display", value: "interactive" },
    { label: "Presentation", value: "slides" },
    { label: "Video", value: "video" },
];

export default function SearchFilter({
    format,
    onFormatChange,
}: SearchFilterProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const selectedOption = formatOptions.find((option) => option.value === format);
    const buttonStyles = format
        ? "bg-accent text-primary-text border-accent"
        : "bg-secondary-bg text-secondary-text border-border hover:border-stone-500";

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleToggle = () => {
        setIsOpen((current) => !current);
    };

    const handleSelect = (optionValue: string) => {
        onFormatChange(optionValue);
        setIsOpen(false);
    };

    return (
        <div className="relative w-full" ref={dropdownRef}>
            <button
                type="button"
                onClick={handleToggle}
                className={`flex h-12 w-full min-w-0 cursor-pointer items-center justify-between rounded-lg border px-4 text-sm font-medium outline-none transition-all duration-300 focus:ring-2 focus:ring-accent/50 ${buttonStyles}`}
            >
                <span className="mr-2 truncate">{selectedOption ? selectedOption.label : "All formats"}</span>
                <svg
                    className={`h-4 w-4 shrink-0 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <ul className="absolute z-50 mt-2 w-full overflow-hidden rounded-lg border border-border bg-secondary-bg shadow-xl animate-in fade-in zoom-in-95 duration-200">
                    {formatOptions.map((option) => (
                        <li key={option.value || "all"}>
                            <button
                                type="button"
                                onClick={() => handleSelect(option.value)}
                                className={`w-full truncate px-4 py-2 text-left text-sm transition-colors duration-200 hover:bg-accent hover:text-primary-text ${
                                    format === option.value ? 'bg-stone-800 font-semibold text-accent' : 'text-secondary-text'
                                }`}
                            >
                                {option.label}
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
