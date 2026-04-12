'use client'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export default function Textarea({
    className = "",
    ...props
}: TextareaProps & { className?: string }) {
        return (
            <textarea
                className={`
                    flex h-35 w-full rounded-xl border px-4 py-3 text-sm
                    bg-secondary-bg border-surface text-primary-text placeholder:text-secondary-text
                    focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                    disabled:cursor-not-allowed disabled:opacity-50
                    transition-all duration-200
                    ${className}
                `}
                {...props}
            />  
        );
    }
    