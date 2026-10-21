import { forwardRef, type InputHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", type = "text", error, disabled, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        disabled={disabled}
        className={`
          flex h-11 w-full rounded-gn-md border bg-gn-bg-card px-4 py-2 text-sm text-gn-text-primary
          placeholder:text-gn-text-muted transition-colors
          gn-focus-ring
          disabled:cursor-not-allowed disabled:opacity-50
          ${error ? "border-gn-error focus-visible:outline-gn-error" : "border-gn-border-default focus-visible:border-gn-border-focus"}
          ${className}
        `}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
