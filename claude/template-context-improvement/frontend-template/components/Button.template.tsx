// Button.tsx - Component template (Keep under 150 lines)
import React from 'react';
import { ButtonProps } from './Button.types';
import { buttonStyles } from './Button.styles';

/**
 * AI NOTE: This is a template for a reusable button component.
 * Follow this pattern for all UI components.
 * Keep component logic minimal - use hooks for complex logic.
 */
export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  onClick,
  className = '',
  ...rest
}) => {
  // Event handlers (keep simple)
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  // Compute classes (consider extracting if complex)
  const classes = [
    buttonStyles.base,
    buttonStyles.variants[variant],
    buttonStyles.sizes[size],
    fullWidth && buttonStyles.fullWidth,
    disabled && buttonStyles.disabled,
    loading && buttonStyles.loading,
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      {...rest}
    >
      {loading && <Spinner className={buttonStyles.spinner} />}
      <span className={buttonStyles.content}>
        {children}
      </span>
    </button>
  );
};

// Button.types.ts - Type definitions (Keep under 50 lines)
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

// Button.styles.ts - Styles (Keep under 80 lines)
export const buttonStyles = {
  base: 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2',
  
  variants: {
    primary: 'bg-blue-600 text-white hover:bg-blue-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    ghost: 'bg-transparent hover:bg-gray-100'
  },
  
  sizes: {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
    xl: 'px-8 py-4 text-xl'
  },
  
  fullWidth: 'w-full',
  disabled: 'opacity-50 cursor-not-allowed',
  loading: 'cursor-wait',
  spinner: 'mr-2',
  content: 'flex items-center'
};

// index.ts - Public API (Keep under 10 lines)
export { Button } from './Button';
export type { ButtonProps } from './Button.types';