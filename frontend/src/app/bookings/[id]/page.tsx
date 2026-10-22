"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { type BookingDetailDto, type BookingStatus } from "@/features/booking/api";

const STEPS: { key: BookingStatus; label: string; icon: string }[] = [
  { key: "confirmed", label: "Confirmed", icon: "✓" },
  { key: "dispatching", label: "Matching Pro", icon: "⚡" },
  { key: "assigned", label: "Specialist Assigned", icon: "👤" },
  { key: "en_route", label: "On The Way", icon: "🛵" },
  { key: "arrived", label: "At Doorstep", icon: "📍" },
  { key: "in_progress", label: "Treatment In Progress", icon: "✨" },
  { key: "completed", label: "Completed", icon: "🎉" },
];

function buildInitialBooking(bookingId: string): BookingDetailDto {
  return {
    id: bookingId,
    booking_number: `GN-20261022-${bookingId.slice(-6).toUpperCase()}`,
    customer_id: "cust_demo_1",
    assigned_professional_id: "pro_1",
    assigned_professional_name: "Kavita Stylist (Senior Artisan)",
    service_id: "srv_hair_spa",
    service_name: "Keratin Deep Conditioning Hair Spa",
    tier_type: "standard",
    booking_type: "instant",
    status: "assigned",
    address_snapshot: {
      address_line1: "Flat 402, Signature Palms, 12th Main",
      city: "Bengaluru",
      state: "Karnataka",
      pincode: "560038",
      latitude: 12.9716,
      longitude: 77.6412,
    },
    scheduled_start_time: null,
    scheduled_end_time: null,
    hold_expires_at: "2026-10-22T05:30:00.000Z",
    start_otp: "4829",
    completion_otp: "9134",
    eta_minutes: 18,
    is_fallback_location: false,
    cancellation_fee_paise: 0,
    price_snapshot: {
      base_rate_paise: 89900,
      add_ons_total_paise: 29900,
      travel_fee_paise: 0,
      discount_applied_paise: 15000,
      taxable_amount_paise: 104800,
      cgst_paise: 9432,
      sgst_paise: 9432,
      total_payable_paise: 123664,
      snapshot_hash: "sha256:d8a9e7f8c9b0e1a2f3d4...",
    },
    items: [
      {
        name: "Keratin Deep Conditioning Hair Spa (STANDARD)",
        item_type: "SERVICE_TIER",
        price_paise: 89900,
        quantity: 1,
      },
      {
        name: "Express De-Tan Pack",
        item_type: "ADD_ON",
        price_paise: 29900,
        quantity: 1,
      },
    ],
    history: [
      {
        from_status: null,
        to_status: "hold_reserved",
        actor_role: "customer",
        reason: "Reservation hold initiated",
        created_at: "2026-10-22T04:45:00.000Z",
      },
      {
        from_status: "hold_reserved",
        to_status: "confirmed",
        actor_role: "customer",
        reason: "Cryptographic HMAC-SHA256 payment verified and captured",
        created_at: "2026-10-22T04:48:00.000Z",
      },
      {
        from_status: "confirmed",
        to_status: "dispatching",
        actor_role: "system",
        reason: "Sector dispatch search triggered across verified partners",
        created_at: "2026-10-22T04:49:00.000Z",
      },
      {
        from_status: "dispatching",
        to_status: "assigned",
        actor_role: "system",
        reason: "Kavita Stylist assigned (ETA: 18 mins, 4.95 Rating)",
        created_at: "2026-10-22T04:50:00.000Z",
      },
    ],
  };
}

function BookingTrackingContent() {
  const params = useParams();
  const bookingId = (params?.id as string) || "mock_id";

  const [booking, setBooking] = useState<BookingDetailDto>(() => buildInitialBooking(bookingId));
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("Change of plans");
  const [isUpdating, setIsUpdating] = useState(false);
  const [rescheduleModalOpen, setRescheduleModalOpen] = useState(false);
  const [selectedNewSlot, setSelectedNewSlot] = useState("Tomorrow, 02:00 PM - 03:00 PM");

  if (!booking) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center space-y-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
          <p className="text-sm text-muted">Loading live booking tracking data...</p>
        </div>
      </div>
    );
  }

  // Current step index
  const activeStepIdx = STEPS.findIndex((s) => s.key === booking.status);

  // Transition handler for live test simulation
  const handleSimulateStatus = (newStatus: BookingStatus, reason: string) => {
    setIsUpdating(true);
    setTimeout(() => {
      setBooking((prev) => {
        if (!prev) return prev;
        const newHistory = [
          ...prev.history,
          {
            from_status: prev.status,
            to_status: newStatus,
            actor_role: newStatus === "cancelled" ? "customer" : "professional",
            reason,
            created_at: new Date().toISOString(),
          },
        ];

        let fee = prev.cancellation_fee_paise;
        if (newStatus === "cancelled" && prev.status === "en_route") {
          fee = 15000; // ₹150 late cancellation fee
        }

        return {
          ...prev,
          status: newStatus,
          cancellation_fee_paise: fee,
          history: newHistory,
        };
      });
      setIsUpdating(false);
    }, 400);
  };

  const handleDeclineAndReassign = () => {
    setIsUpdating(true);
    setTimeout(() => {
      setBooking((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          assigned_professional_name: "Meera Stylist (Reassigned Specialist)",
          assigned_professional_id: "pro_2",
          eta_minutes: 24,
          history: [
            ...prev.history,
            {
              from_status: "assigned",
              to_status: "dispatching",
              actor_role: "professional",
              reason: "Kavita Stylist declined offer (Vehicle maintenance)",
              created_at: new Date().toISOString(),
            },
            {
              from_status: "dispatching",
              to_status: "assigned",
              actor_role: "system",
              reason: "Reassigned to Meera Stylist (ETA: 24 mins, 4.80 Rating)",
              created_at: new Date().toISOString(),
            },
          ],
        };
      });
      setIsUpdating(false);
    }, 500);
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
      {/* Top Breadcrumb & Status Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-6">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/" className="text-xs text-muted hover:text-foreground">
              ← Back to Catalog
            </Link>
            <span className="text-muted text-xs">•</span>
            <span className="text-xs font-mono text-primary font-bold">{booking.booking_number}</span>
          </div>
          <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
            Live Booking &amp; Dispatch Tracker
          </h1>
          <p className="mt-1 text-sm text-muted">
            {booking.service_name} • {booking.tier_type.toUpperCase()}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge
            variant="outline"
            className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wider ${
              booking.status === "completed"
                ? "border-emerald-500 bg-emerald-500/10 text-emerald-500"
                : booking.status === "cancelled"
                ? "border-red-500 bg-red-500/10 text-red-500"
                : "border-primary bg-primary/10 text-primary animate-pulse"
            }`}
          >
            ● {booking.status.replace("_", " ")}
          </Badge>

          {booking.status !== "completed" && booking.status !== "cancelled" && (
            <Button variant="outline" size="sm" onClick={() => setCancelModalOpen(true)}>
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Real-time State Machine Stepper */}
      <div className="rounded-2xl border border-card-border bg-card p-6 shadow-sm">
        <h3 className="text-xs font-bold tracking-wider uppercase text-muted mb-6">
          Lifecycle State Machine
        </h3>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 md:grid-cols-7">
          {STEPS.map((step, idx) => {
            const isCompleted = activeStepIdx > idx;
            const isCurrent = activeStepIdx === idx;

            return (
              <div key={step.key} className="flex flex-col items-center text-center">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-bold transition-all ${
                    isCurrent
                      ? "bg-primary text-white ring-4 ring-primary/20 scale-105 shadow-md shadow-primary/20"
                      : isCompleted
                      ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/40"
                      : "bg-muted/10 text-muted border border-card-border"
                  }`}
                >
                  {isCompleted ? "✓" : step.icon}
                </div>
                <span
                  className={`mt-2 text-xs font-medium ${
                    isCurrent
                      ? "font-bold text-foreground"
                      : isCompleted
                      ? "text-foreground/80"
                      : "text-muted"
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Grid: ETA & Pro Info + OTP Handoff */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: ETA & Pro Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Arrival & Credible ETA Banner */}
          <div className="rounded-2xl border border-card-border bg-gradient-to-br from-card to-card/50 p-6 shadow-sm">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-muted">
                  Operational Arrival Estimate
                </span>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold text-foreground">
                    ~{booking.eta_minutes ?? 18}
                  </span>
                  <span className="text-lg font-bold text-primary">Minutes</span>
                </div>
                <p className="mt-1 text-xs text-muted">
                  Calculated from live GPS telemetry: {booking.address_snapshot.address_line1}
                </p>
              </div>

              <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 text-[11px] text-amber-500 max-w-xs">
                <strong>Credible ETA Guarantee:</strong> GlamNow strictly forbids 10-minute arrival claims based on
                configuration alone. Real travel time is verified per ADR-0003.
              </div>
            </div>
          </div>

          {/* Assigned Professional Profile Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-muted">
                    Assigned Specialist
                  </span>
                  <CardTitle className="text-lg mt-0.5">{booking.assigned_professional_name}</CardTitle>
                </div>
                <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 font-semibold text-xs">
                  ✓ Verified Artisan
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 border-t border-b border-card-border py-4 text-center text-xs">
                <div>
                  <span className="text-muted block">Rating</span>
                  <strong className="text-sm font-bold text-foreground">★ 4.95</strong>
                </div>
                <div>
                  <span className="text-muted block">Experience</span>
                  <strong className="text-sm font-bold text-foreground">8 Years</strong>
                </div>
                <div>
                  <span className="text-muted block">Kit Sanitization</span>
                  <strong className="text-sm font-bold text-emerald-500">100% Sterile</strong>
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <Button variant="outline" size="sm" className="w-full text-xs" onClick={() => alert("Connecting to partner via masked proxy...")}>
                  📞 Call Specialist
                </Button>
                <Button variant="outline" size="sm" className="w-full text-xs" onClick={() => alert("Opening secure chat...")}>
                  💬 Message
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Interactive Simulation Controls (For Phase 6 Demo & Testing) */}
          <div className="rounded-2xl border border-dashed border-primary/40 bg-primary/5 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-foreground text-sm">🧪 Interactive Dispatch Testing Console</h4>
                <p className="text-xs text-muted">
                  Simulate real-time specialist and dispatch state transitions to verify end-to-end rules.
                </p>
              </div>
              <Badge variant="outline" className="text-[10px] font-mono">
                DEMO CONTROLS
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start"
                disabled={isUpdating || booking.status !== "assigned"}
                onClick={() => handleSimulateStatus("en_route", "Specialist started travel")}
              >
                1. Pro Accept (En Route)
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start text-amber-500 border-amber-500/30 hover:bg-amber-500/10"
                disabled={isUpdating || booking.status !== "assigned"}
                onClick={handleDeclineAndReassign}
              >
                Decline &amp; Reassign
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start"
                disabled={isUpdating || booking.status !== "en_route"}
                onClick={() => handleSimulateStatus("arrived", "Partner arrived at customer doorstep")}
              >
                2. Partner Arrived
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start"
                disabled={isUpdating || booking.status !== "arrived"}
                onClick={() => handleSimulateStatus("in_progress", "Verified start OTP 4829")}
              >
                3. Verify Start OTP
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/10"
                disabled={isUpdating || booking.status !== "in_progress"}
                onClick={() => handleSimulateStatus("completed", "Verified completion OTP 9134")}
              >
                4. Complete Service
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="text-xs justify-start"
                onClick={() => setRescheduleModalOpen(true)}
              >
                Reschedule (&gt;2h SLA)
              </Button>
            </div>
          </div>
        </div>

        {/* Right Column: OTPs & Summary */}
        <div className="space-y-6">
          {/* OTP Verification Card */}
          <Card className="border-primary/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted">
                Doorstep Security OTPs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-xl bg-primary/10 border border-primary/20 p-4 text-center">
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted block">
                  Service Start OTP
                </span>
                <span className="text-3xl font-mono font-black text-primary tracking-widest block mt-1">
                  {booking.start_otp}
                </span>
                <p className="mt-1.5 text-[11px] text-muted">
                  Share this OTP with your specialist before service begins.
                </p>
              </div>

              <div className="rounded-xl bg-card-border/30 border border-card-border p-4 text-center">
                <span className="text-[11px] font-bold uppercase tracking-wider text-muted block">
                  Completion Verification OTP
                </span>
                <span className="text-3xl font-mono font-black text-foreground tracking-widest block mt-1">
                  {booking.completion_otp}
                </span>
                <p className="mt-1.5 text-[11px] text-muted">
                  Share this OTP only when service is fully completed.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Price Snapshot & Order Details */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted">
                Order Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-muted">Base Rate:</span>
                <span className="font-medium text-foreground">
                  ₹{(booking.price_snapshot.base_rate_paise / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Add-ons:</span>
                <span className="font-medium text-foreground">
                  ₹{(booking.price_snapshot.add_ons_total_paise / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Travel &amp; Delivery:</span>
                <span className="text-emerald-500 font-medium">FREE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Discount Applied:</span>
                <span className="text-emerald-500 font-medium">
                  -₹{(booking.price_snapshot.discount_applied_paise / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">GST (18%):</span>
                <span className="text-foreground">
                  ₹{((booking.price_snapshot.cgst_paise + booking.price_snapshot.sgst_paise) / 100).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between pt-2 border-t font-bold text-foreground text-sm">
                <span>Total Paid:</span>
                <span className="text-primary">
                  ₹{(booking.price_snapshot.total_payable_paise / 100).toFixed(2)}
                </span>
              </div>
              {booking.cancellation_fee_paise > 0 && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-2 text-xs text-red-500">
                  Late Cancellation Fee: ₹{(booking.cancellation_fee_paise / 100).toFixed(2)}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Auditable Event History */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold uppercase tracking-wider text-muted">
                Auditable Event History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {booking.history.map((h, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs">
                    <span className="mt-1 h-2 w-2 rounded-full bg-primary shrink-0" />
                    <div>
                      <span className="font-semibold text-foreground uppercase tracking-wider text-[10px]">
                        {h.to_status}
                      </span>
                      <p className="text-muted text-[11px]">{h.reason}</p>
                      <span className="text-[10px] text-muted/70 font-mono">
                        Actor: {h.actor_role} • {new Date(h.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Cancellation Modal with SLA rules */}
      <Dialog
        open={cancelModalOpen}
        onClose={() => setCancelModalOpen(false)}
        title="Cancel Booking"
      >
        <div className="space-y-4 text-xs">
          <p className="text-muted">
            Please review our cancellation policy:
          </p>
          <div className="rounded-xl border border-card-border p-3 space-y-1.5 bg-card/40">
            <div className="flex justify-between">
              <span className="text-muted">Current Status:</span>
              <span className="font-bold text-foreground uppercase">{booking.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Cancellation Fee:</span>
              <span className="font-bold text-emerald-500">
                {booking.status === "en_route" ? "₹150.00 (Late fee once en route)" : "₹0.00 (100% Free refund)"}
              </span>
            </div>
          </div>

          <div>
            <label className="block mb-1 font-medium text-foreground">Reason for cancellation</label>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full rounded-md border border-card-border bg-background p-2 text-xs text-foreground"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCancelModalOpen(false)}>
              Keep Booking
            </Button>
            <Button
              variant="outline"
              className="text-red-500 border-red-500 hover:bg-red-500/10"
              onClick={() => {
                setCancelModalOpen(false);
                handleSimulateStatus("cancelled", cancelReason);
              }}
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Reschedule Modal (>2h advance SLA) */}
      <Dialog
        open={rescheduleModalOpen}
        onClose={() => setRescheduleModalOpen(false)}
        title="Reschedule Booking"
      >
        <div className="space-y-4 text-xs">
          <p className="text-muted">
            Free rescheduling is permitted when requested at least 2 hours prior to scheduled appointment.
          </p>
          <div>
            <label className="block mb-1 font-medium text-foreground">Select New Slot</label>
            <select
              value={selectedNewSlot}
              onChange={(e) => setSelectedNewSlot(e.target.value)}
              className="w-full rounded-md border border-card-border bg-background p-2 text-xs text-foreground"
            >
              <option>Tomorrow, 02:00 PM - 03:00 PM</option>
              <option>Tomorrow, 05:00 PM - 06:00 PM</option>
              <option>Day After, 10:00 AM - 11:00 AM</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setRescheduleModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                setRescheduleModalOpen(false);
                handleSimulateStatus("assigned", `Rescheduled to ${selectedNewSlot}`);
              }}
            >
              Confirm New Slot
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

export default function BookingTrackingPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="text-center space-y-2">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
            <p className="text-sm text-muted">Loading live booking tracking data...</p>
          </div>
        </div>
      }
    >
      <BookingTrackingContent />
    </Suspense>
  );
}
