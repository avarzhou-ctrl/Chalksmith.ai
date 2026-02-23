import React from 'react';

// We define what props the button can accept
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  isLoading?: boolean;
}

export default function Button({ 
  children, 
  variant = 'primary', 
  isLoading = false, 
  className = '',
  ...props 
}: ButtonProps) {
  
  // base style for buttons
  const baseStyles = "inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed";
  
  // amber style
  const primaryStyles = "bg-accent hover:bg-amber-700 text-primary-text";
  
  // dark gray style
  const secondaryStyles = "bg-surface hover:bg-stone-600 text-primary-text border border-[#57534e]";

  // choose the style based on the 'variant' prop
  const variantStyles = variant === 'primary' ? primaryStyles : secondaryStyles;

  return (
    <button 
      className={"my_button"}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? (
        // simple CSS spinner for the loading state
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : null}
      {children}
    </button>
  );
}