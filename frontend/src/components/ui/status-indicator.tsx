import { forwardRef, type HTMLAttributes } from "react";

export type OrderStatus =
  | "pending"
  | "hold_reserved"
  | "confirmed"
  | "dispatched"
  | "arrived"
  | "otp_verified"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "rework_requested";

export interface StatusIndicatorProps extends HTMLAttributes<HTMLSpanElement> {
  status: OrderStatus;
  pulse?: boolean;
}

const statusConfig: Record<
  OrderStatus,
  { label: string; bg: string; text: string; dot: string }
> = {
  pending: {
    label: "Pending Hold",
    bg: "bg-amber-50 border-amber-200",
    text: "text-amber-800",
    dot: "bg-amber-500",
  },
  hold_reserved: {
    label: "Slot Reserved (10m)",
    bg: "bg-amber-50 border-amber-200",
    text: "text-amber-800",
    dot: "bg-amber-500",
  },
  confirmed: {
    label: "Booking Confirmed",
    bg: "bg-blue-50 border-blue-200",
    text: "text-blue-800",
    dot: "bg-blue-500",
  },
  dispatched: {
    label: "Pro En Route",
    bg: "bg-indigo-50 border-indigo-200",
    text: "text-indigo-800",
    dot: "bg-indigo-500",
  },
  arrived: {
    label: "At Your Doorstep",
    bg: "bg-purple-50 border-purple-200",
    text: "text-purple-800",
    dot: "bg-purple-500",
  },
  otp_verified: {
    label: "OTP Verified",
    bg: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-800",
    dot: "bg-emerald-500",
  },
  in_progress: {
    label: "Service In Progress",
    bg: "bg-emerald-50 border-emerald-200",
    text: "text-emerald-800",
    dot: "bg-emerald-500",
  },
  completed: {
    label: "Completed",
    bg: "bg-gn-success-subtle border-gn-success/20",
    text: "text-gn-success",
    dot: "bg-gn-success",
  },
  cancelled: {
    label: "Cancelled",
    bg: "bg-gn-error-subtle border-gn-error/20",
    text: "text-gn-error",
    dot: "bg-gn-error",
  },
  rework_requested: {
    label: "Alteration Rework",
    bg: "bg-orange-50 border-orange-200",
    text: "text-orange-800",
    dot: "bg-orange-500",
  },
};

export const StatusIndicator = forwardRef<HTMLSpanElement, StatusIndicatorProps>(
  ({ status, pulse = true, className = "", ...props }, ref) => {
    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span
        ref={ref}
        className={`
          inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-gn-full text-xs font-semibold border
          ${config.bg} ${config.text} ${className}
        `}
        {...props}
      >
        <span
          className={`h-2 w-2 rounded-full ${config.dot} ${pulse ? "gn-pulse" : ""}`}
          aria-hidden="true"
        />
        <span>{config.label}</span>
      </span>
    );
  }
);
StatusIndicator.displayName = "StatusIndicator";
