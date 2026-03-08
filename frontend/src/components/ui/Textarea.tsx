'use client'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

export default function Textarea({
    ...props
}: TextareaProps) {
    return (
        <textarea
            className={`
                /* Layout */
                flex min-h-30 w-full rounded-md border px-4 py-3 text-sm
                
                /* Chalkboard colors */
                bg-secondary-bg border-surface text-primary-text placeholder:text-secondary-text
                
                /* Selection focus */
                focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                
                /* Interaction states */
                disabled:cursor-not-allowed disabled:opacity-50
                transition-all duration-200
            `}
            {...props}
        />  
    );
}