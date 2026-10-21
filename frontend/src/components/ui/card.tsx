import { forwardRef, type HTMLAttributes } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className = "", hover = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          bg-gn-bg-card text-gn-text-primary rounded-gn-lg border border-gn-border-default shadow-gn-sm
          ${hover ? "transition-all duration-[var(--gn-transition-base)] hover:shadow-gn-md hover:border-gn-border-strong hover:-translate-y-0.5" : ""}
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => (
    <div ref={ref} className={`flex flex-col space-y-1.5 p-6 ${className}`} {...props}>
      {children}
    </div>
  )
);
CardHeader.displayName = "CardHeader";

const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className = "", children, ...props }, ref) => (
    <h3
      ref={ref}
      className={`font-semibold text-lg sm:text-xl text-gn-text-primary tracking-tight ${className}`}
      {...props}
    >
      {children}
    </h3>
  )
);
CardTitle.displayName = "CardTitle";

const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className = "", children, ...props }, ref) => (
    <p ref={ref} className={`text-sm text-gn-text-secondary leading-relaxed ${className}`} {...props}>
      {children}
    </p>
  )
);
CardDescription.displayName = "CardDescription";

const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => (
    <div ref={ref} className={`p-6 pt-0 ${className}`} {...props}>
      {children}
    </div>
  )
);
CardContent.displayName = "CardContent";

const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => (
    <div ref={ref} className={`flex items-center p-6 pt-0 ${className}`} {...props}>
      {children}
    </div>
  )
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };
