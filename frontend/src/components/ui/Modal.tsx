'use client'

import { useEffect } from "react";
import Button from "./Button";
import { X } from 'lucide-react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
}

export default function Modal({
    isOpen,
    onClose,
    title,
    children
}: ModalProps) {
    // Close on 'Esc' key
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handleEsc);
        return () => window.removeEventListener("keydown", handleEsc);
    }, [onClose]);

  if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            { /* Overlay */ }
            <div 
                className="absolute inset-0 bg-stone-950/70 backdrop-blur-[2px] transition-opacity" 
                onClick={onClose} 
            />

            { /* Modal Content */ }
            <div className="relative z-10 flex max-h-[calc(100dvh-2rem)] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-border bg-secondary-bg pt-8 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-1.5 hover:bg-surface/50 rounded-lg text-secondary-text transition-colors"
                >
                    <X size={20} />
                </button>

                {/* Header */}
                <div className="mb-6 shrink-0 px-8 text-center">
                    <h2 className="text-xl font-bold text-primary-text">{title}</h2>
                </div>

                {/* Message */}
                <div className="min-h-0 overflow-y-auto px-8 pb-10 text-center leading-relaxed text-secondary-text">
                    {children}
                </div>
            </div>
        </div>
    );
}
