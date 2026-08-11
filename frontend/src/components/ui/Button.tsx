'use client'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'outline';
    size?: 'sm' | 'md' | 'lg';
}

export default function Button({
    children, 
    variant = 'primary', 
    size = 'md',
    className = "",
    ...props
}: ButtonProps) {
    const baseClasses = "rounded-xl font-medium transition-colors duration-300 flex items-center justify-center";

    const styles = {
        primary: "bg-accent text-primary-text hover:bg-amber-700 disabled:bg-stone-800 disabled:text-stone-500",
        secondary: "bg-surface text-secondary-text hover:bg-stone-500",
        outline: "border border-border bg-transparent text-secondary-text hover:border-accent hover:text-accent disabled:opacity-50",
    }

    const sizes = {
        sm: "px-3 py-1.5 text-xs",
        md: "px-4 py-2 text-sm",
        lg: "px-6 py-3 text-base",
    }

    const opacityStyle = props.disabled ? "opacity-50 cursor-not-allowed" : "opacity-100 cursor-pointer";

    const combinedClassName = `${baseClasses} ${styles[variant]} ${sizes[size]} ${opacityStyle} ${className}`;

    return (
        <button {...props} className={combinedClassName}>
            {children}
        </button>
    );
}
