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
            <div className="relative bg-secondary-bg border border-border rounded-2xl shadow-2xl w-full max-w-md pt-8 px-8 pb-10 z-10 animate-in fade-in zoom-in-95 duration-200">
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-1.5 hover:bg-surface/50 rounded-lg text-secondary-text transition-colors"
                >
                    <X size={20} />
                </button>

                {/* Header */}
                <div className="mb-6 text-center">
                    <h2 className="text-xl font-bold text-primary-text">{title}</h2>
                </div>

                {/* Message */}
                <div className="text-center text-secondary-text leading-relaxed">
                    {children}
                </div>
            </div>
        </div>
    );
}
