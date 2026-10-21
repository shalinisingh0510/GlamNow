import { forwardRef, type HTMLAttributes } from "react";

export type BadgeVariant =
  | "default"
  | "primary"
  | "secondary"
  | "outline"
  | "success"
  | "warning"
  | "error"
  | "basic"
  | "standard"
  | "premium";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-gn-bg-secondary text-gn-text-secondary border-transparent",
  primary: "bg-gn-accent-primary-subtle text-gn-accent-primary border-transparent font-semibold",
  secondary: "bg-gn-accent-secondary-subtle text-gn-accent-secondary-hover border-transparent font-medium",
  outline: "bg-transparent text-gn-text-secondary border-gn-border-default",
  success: "bg-gn-success-subtle text-gn-success border-transparent font-medium",
  warning: "bg-gn-warning-subtle text-gn-warning border-transparent font-medium",
  error: "bg-gn-error-subtle text-gn-error border-transparent font-medium",
  basic: "bg-zinc-100 text-zinc-700 border-zinc-200 font-medium",
  standard: "bg-amber-50 text-amber-800 border-amber-200 font-medium",
  premium: "bg-gradient-to-r from-purple-900 to-indigo-900 text-amber-200 border-amber-400/30 shadow-xs font-semibold",
};

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className = "", variant = "default", children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center px-2.5 py-0.5 rounded-gn-full text-xs font-medium border
          transition-colors duration-[var(--gn-transition-fast)]
          ${variantStyles[variant]}
          ${className}
        `}
        {...props}
      >
        {children}
      </span>
    );
  }
);
Badge.displayName = "Badge";

export { Badge };
