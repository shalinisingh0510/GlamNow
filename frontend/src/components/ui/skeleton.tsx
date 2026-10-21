import { forwardRef, type HTMLAttributes } from "react";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "rectangular" | "circular";
  width?: string | number;
  height?: string | number;
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = "rectangular", width, height, className = "", style, ...props }, ref) => {
    const variantClass =
      variant === "circular"
        ? "rounded-full"
        : variant === "text"
        ? "rounded-gn-sm h-4 w-full"
        : "rounded-gn-md";

    return (
      <div
        ref={ref}
        className={`gn-skeleton ${variantClass} ${className}`}
        style={{
          width: width,
          height: height,
          ...style,
        }}
        {...props}
      />
    );
  }
);
Skeleton.displayName = "Skeleton";

export function CardSkeleton() {
  return (
    <div className="p-6 rounded-gn-lg border border-gn-border-default bg-gn-bg-card space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="space-y-2 flex-1">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="rectangular" height={80} />
      <div className="flex justify-between items-center pt-2">
        <Skeleton variant="text" width="30%" />
        <Skeleton variant="rectangular" width={100} height={36} />
      </div>
    </div>
  );
}
