import { forwardRef, type ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-gn-accent-primary text-gn-text-inverse hover:bg-gn-accent-primary-hover active:scale-[0.98] shadow-gn-sm hover:shadow-gn-md",
  secondary:
    "bg-gn-accent-secondary text-gn-text-inverse hover:bg-gn-accent-secondary-hover active:scale-[0.98] shadow-gn-sm hover:shadow-gn-md",
  ghost:
    "bg-transparent text-gn-text-secondary hover:bg-gn-bg-secondary active:bg-gn-bg-tertiary",
  danger:
    "bg-gn-error text-gn-text-inverse hover:opacity-90 active:scale-[0.98] shadow-gn-sm",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm rounded-gn-sm gap-1.5",
  md: "h-10 px-5 text-sm rounded-gn-md gap-2",
  lg: "h-12 px-6 text-base rounded-gn-lg gap-2.5",
};

/**
 * Accessible button primitive with loading and variant support.
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, disabled, children, className = "", ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`
          inline-flex items-center justify-center font-medium
          transition-all duration-[var(--gn-transition-fast)]
          gn-focus-ring
          disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${className}
        `}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
export { Button };
export type { ButtonProps, ButtonVariant, ButtonSize };
