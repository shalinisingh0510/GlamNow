import { forwardRef, type HTMLAttributes } from "react";

export interface RatingProps extends HTMLAttributes<HTMLDivElement> {
  score: number;
  reviewCount?: number;
  size?: "sm" | "md" | "lg";
  showNumber?: boolean;
}

const sizeClasses = {
  sm: "w-3.5 h-3.5 text-xs",
  md: "w-4 h-4 text-sm",
  lg: "w-5 h-5 text-base",
};

export const Rating = forwardRef<HTMLDivElement, RatingProps>(
  ({ score, reviewCount, size = "md", showNumber = true, className = "", ...props }, ref) => {
    const fullStars = Math.floor(score);
    const hasHalfStar = score - fullStars >= 0.5;

    return (
      <div ref={ref} className={`inline-flex items-center gap-1.5 ${className}`} {...props}>
        <div className="flex items-center text-amber-500">
          {[1, 2, 3, 4, 5].map((index) => {
            if (index <= fullStars) {
              return (
                <svg
                  key={index}
                  className={`${sizeClasses[size].split(" ")[0]} ${sizeClasses[size].split(" ")[1]} fill-current`}
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              );
            } else if (index === fullStars + 1 && hasHalfStar) {
              return (
                <svg
                  key={index}
                  className={`${sizeClasses[size].split(" ")[0]} ${sizeClasses[size].split(" ")[1]} fill-current text-amber-500`}
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <defs>
                    <linearGradient id={`half-${index}`}>
                      <stop offset="50%" stopColor="currentColor" />
                      <stop offset="50%" stopColor="#D1C4BA" />
                    </linearGradient>
                  </defs>
                  <path
                    fill={`url(#half-${index})`}
                    d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                  />
                </svg>
              );
            } else {
              return (
                <svg
                  key={index}
                  className={`${sizeClasses[size].split(" ")[0]} ${sizeClasses[size].split(" ")[1]} fill-current text-gn-border-strong`}
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              );
            }
          })}
        </div>

        {showNumber && (
          <span className="font-bold text-gn-text-primary text-xs sm:text-sm">
            {score.toFixed(2)}
          </span>
        )}

        {reviewCount !== undefined && (
          <span className="text-gn-text-tertiary text-xs">
            ({reviewCount} reviews)
          </span>
        )}
      </div>
    );
  }
);
Rating.displayName = "Rating";
