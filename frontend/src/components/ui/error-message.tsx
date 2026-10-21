import { Button } from "./button";

export interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorMessage({
  title = "Something went wrong",
  message,
  onRetry,
  className = "",
}: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className={`
        p-4 rounded-gn-md border border-gn-error/30 bg-gn-error-subtle text-gn-error
        flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3
        ${className}
      `}
    >
      <div className="flex items-start gap-3">
        <svg className="w-5 h-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <h4 className="font-semibold text-sm">{title}</h4>
          <p className="text-xs text-gn-error/90 mt-0.5">{message}</p>
        </div>
      </div>

      {onRetry && (
        <Button
          variant="danger"
          size="sm"
          onClick={onRetry}
          className="shrink-0 text-xs h-8"
        >
          Try Again
        </Button>
      )}
    </div>
  );
}
