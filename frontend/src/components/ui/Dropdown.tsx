'use client';

import { useState, useRef, useEffect } from 'react';

interface Option {
    label: string;
    value: string;
}

interface DropdownProps {
    options: readonly Option[];
    value: string;
    onChange: (value: string) => void;
    placeholder: string;
    disabled?: boolean;
    variant?: 'default' | 'search';
}

export default function Dropdown({
    options,
    value,
    onChange,
    placeholder = "Select an option",
    disabled = false,
    variant = 'default',
}: DropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const selectedOption = options.find(opt => opt.value === value);

    const handleToggle = () => {
        if (!disabled) setIsOpen(!isOpen);
    };

    const handleSelect = (optionValue: string) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    // The "Amber Theme" logic: 
    // If a value is selected, use the accent (amber) color.
    const buttonStyles = value 
        ? "bg-accent text-primary-text border-accent" 
        : "bg-secondary-bg text-secondary-text border-border hover:border-stone-500";

    const disabledStyles = disabled 
        ? "opacity-40 cursor-not-allowed" 
        : "cursor-pointer";
    const triggerStyles = variant === 'search' ? 'h-12 rounded-lg px-4' : 'rounded-xl px-4 py-2';
    const menuStyles = variant === 'search' ? 'rounded-lg' : 'rounded-xl';

    return (
        <div className="relative w-full" ref={dropdownRef}>
            <button
                type="button"
                onClick={handleToggle}
                disabled={disabled}
                className={`flex w-full min-w-0 items-center justify-between border text-sm font-medium outline-none transition-all duration-300 focus:ring-2 focus:ring-accent/50 ${triggerStyles} ${buttonStyles} ${disabledStyles}`}
            >
                <span className="truncate mr-2">{selectedOption ? selectedOption.label : placeholder}</span>
                <svg 
                    className={`w-4 h-4 transition-transform duration-300 shrink-0 ${isOpen ? 'rotate-180' : ''}`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {isOpen && (
                <ul className={`absolute z-50 mt-2 w-full overflow-hidden border border-border bg-secondary-bg shadow-xl animate-in fade-in zoom-in-95 duration-200 ${menuStyles}`}>
                    {options.map((option) => (
                        <li key={option.value}>
                            <button
                                onClick={() => handleSelect(option.value)}
                                className={`w-full text-left px-4 py-2 text-sm transition-colors duration-200 hover:bg-accent hover:text-primary-text truncate ${
                                    value === option.value ? 'bg-stone-800 text-accent font-semibold' : 'text-secondary-text'
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
