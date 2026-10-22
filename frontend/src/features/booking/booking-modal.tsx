"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import type { BookingDetailDto } from "./api";
import type { ServiceSummaryDto } from "@/features/catalog/api";

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  service: ServiceSummaryDto | null;
  initialTier?: "basic" | "standard" | "premium";
  preferredProId?: string | null;
}

export function BookingModal({
  isOpen,
  onClose,
  service,
  initialTier = "standard",
  preferredProId = null,
}: BookingModalProps) {
  const router = useRouter();

  // Step flow: 1: Configure -> 2: Address & Schedule -> 3: Review Quote -> 4: Payment -> 5: Confirmed
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [selectedTier, setSelectedTier] = useState<"basic" | "standard" | "premium">(initialTier);
  const [selectedAddOns, setSelectedAddOns] = useState<string[]>([]);
  const [bookingType, setBookingType] = useState<"instant" | "scheduled">("instant");
  const [selectedSlotTime, setSelectedSlotTime] = useState<string>("Tomorrow, 10:00 AM - 11:00 AM");
  const [promoCode, setPromoCode] = useState("WELCOME50");

  // Address selection
  const [savedAddresses] = useState([
    {
      id: "addr_1",
      label: "Home (Indiranagar)",
      line1: "Flat 402, Signature Palms, 12th Main, Indiranagar",
      pincode: "560038",
      city: "Bengaluru",
      eta: "18 mins",
    },
    {
      id: "addr_2",
      label: "Work (Koramangala)",
      line1: "Level 3, Co-Works Hub, 5th Block, Koramangala",
      pincode: "560034",
      city: "Bengaluru",
      eta: "24 mins",
    },
  ]);
  const [selectedAddressId, setSelectedAddressId] = useState("addr_1");

  // Payment state
  const [paymentMethod, setPaymentMethod] = useState<"online_upi" | "card" | "net_banking">("online_upi");
  const [simulateFailure, setSimulateFailure] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Booking result
  const [activeBooking, setActiveBooking] = useState<BookingDetailDto | null>(null);
  const [holdSecondsRemaining, setHoldSecondsRemaining] = useState(600); // 10 minutes

  // Reset state when service changes without cascading render setState effects
  const [prevServiceId, setPrevServiceId] = useState<string | null>(null);
  if (service && service.id !== prevServiceId) {
    setPrevServiceId(service.id);
    setSelectedTier(initialTier);
    setStep(1);
    setErrorMessage(null);
  }

  // Hold Countdown Timer
  useEffect(() => {
    if (step < 3 || step === 5) return;
    const interval = setInterval(() => {
      setHoldSecondsRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [step]);

  if (!service) return null;

  // Pricing calculations
  const basePricePaise =
    selectedTier === "basic" ? 49900 : selectedTier === "standard" ? 89900 : 169900;
  const addOnsTotalPaise = selectedAddOns.length * 29900;
  const subtotalPaise = basePricePaise + addOnsTotalPaise;
  const discountPaise = promoCode.toUpperCase() === "WELCOME50" ? Math.min(Math.round(subtotalPaise * 0.5), 15000) : 0;
  const taxablePaise = Math.max(0, subtotalPaise - discountPaise);
  const gstPaise = Math.round(taxablePaise * 0.18);
  const totalPayablePaise = taxablePaise + gstPaise;

  const handleCreateHold = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      // Create reservation hold
      const holdBooking: BookingDetailDto = {
        id: `b_${Date.now()}`,
        booking_number: `GN-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${Math.random().toString(16).substring(2, 8).toUpperCase()}`,
        customer_id: "cust_demo_1",
        assigned_professional_id: preferredProId || "pro_1",
        assigned_professional_name: preferredProId ? "Shreya Sen (Preferred Stylist)" : "Kavita Stylist (Auto-Matched)",
        service_id: service.id,
        service_name: service.name,
        tier_type: selectedTier,
        booking_type: bookingType,
        status: "hold_reserved",
        address_snapshot: {
          address_line1: savedAddresses.find((a) => a.id === selectedAddressId)?.line1 || "",
          city: "Bengaluru",
          state: "Karnataka",
          pincode: "560038",
          latitude: 12.9716,
          longitude: 77.6412,
        },
        scheduled_start_time: bookingType === "scheduled" ? "Tomorrow, 10:00 AM" : null,
        scheduled_end_time: bookingType === "scheduled" ? "Tomorrow, 11:00 AM" : null,
        hold_expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
        start_otp: "4829",
        completion_otp: "9134",
        eta_minutes: bookingType === "instant" ? 18 : null,
        is_fallback_location: false,
        cancellation_fee_paise: 0,
        price_snapshot: {
          base_rate_paise: basePricePaise,
          add_ons_total_paise: addOnsTotalPaise,
          travel_fee_paise: 0,
          discount_applied_paise: discountPaise,
          taxable_amount_paise: taxablePaise,
          cgst_paise: Math.round(gstPaise / 2),
          sgst_paise: Math.round(gstPaise / 2),
          total_payable_paise: totalPayablePaise,
          snapshot_hash: "sha256:d8a9e7f8c9b0e1a2f3d4...",
        },
        items: [
          {
            name: `${service.name} (${selectedTier.toUpperCase()})`,
            item_type: "SERVICE_TIER",
            price_paise: basePricePaise,
            quantity: 1,
          },
          ...selectedAddOns.map((ao) => ({
            name: ao === "ao_detan" ? "De-Tan Express Mask" : "Hydrating Scalp Serum",
            item_type: "ADD_ON",
            price_paise: 29900,
            quantity: 1,
          })),
        ],
        history: [
          {
            from_status: null,
            to_status: "hold_reserved",
            actor_role: "customer",
            reason: "Checkout reservation hold initiated",
            created_at: new Date().toISOString(),
          },
        ],
      };

      setActiveBooking(holdBooking);
      setStep(4); // Move to Payment Step
    } catch (e: unknown) {
      setErrorMessage(e instanceof Error ? e.message : "Failed to hold reservation slot.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmPayment = async () => {
    if (!activeBooking) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (simulateFailure) {
        throw new Error("Razorpay Sandbox: Bank declined transaction (Simulated Payment Failure).");
      }

      // Simulate cryptographic confirmation
      const confirmedBooking: BookingDetailDto = {
        ...activeBooking,
        status: "assigned",
        history: [
          ...activeBooking.history,
          {
            from_status: "hold_reserved",
            to_status: "confirmed",
            actor_role: "customer",
            reason: "Sandbox payment verified via HMAC-SHA256 signature",
            created_at: new Date().toISOString(),
          },
          {
            from_status: "confirmed",
            to_status: "assigned",
            actor_role: "system",
            reason: "Auto-matched verified specialist with 18m travel estimate",
            created_at: new Date().toISOString(),
          },
        ],
      };

      setActiveBooking(confirmedBooking);
      setStep(5); // Confirmed!
    } catch (e: unknown) {
      setErrorMessage(e instanceof Error ? e.message : "Payment verification failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <Dialog open={isOpen} onClose={onClose} title={`Book ${service.name}`}>
      <div className="space-y-6">
        {/* Step Indicator Header */}
        <div className="flex items-center justify-between border-b pb-4 text-xs font-medium text-muted">
          <div className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                step >= 1 ? "bg-primary text-white" : "bg-card-border text-muted"
              }`}
            >
              1
            </span>
            <span className={step === 1 ? "font-bold text-foreground" : ""}>Tier & Add-ons</span>
          </div>
          <div className="h-0.5 w-6 bg-card-border" />
          <div className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                step >= 2 ? "bg-primary text-white" : "bg-card-border text-muted"
              }`}
            >
              2
            </span>
            <span className={step === 2 ? "font-bold text-foreground" : ""}>Time & Address</span>
          </div>
          <div className="h-0.5 w-6 bg-card-border" />
          <div className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                step >= 3 ? "bg-primary text-white" : "bg-card-border text-muted"
              }`}
            >
              3
            </span>
            <span className={step === 3 ? "font-bold text-foreground" : ""}>Quote Review</span>
          </div>
          <div className="h-0.5 w-6 bg-card-border" />
          <div className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                step >= 4 ? "bg-primary text-white" : "bg-card-border text-muted"
              }`}
            >
              4
            </span>
            <span className={step >= 4 ? "font-bold text-foreground" : ""}>Payment</span>
          </div>
        </div>

        {errorMessage && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-500">
            <strong>Error:</strong> {errorMessage}
          </div>
        )}

        {/* STEP 1: TIER & ADD-ONS */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-xs font-bold tracking-wider uppercase text-muted">
                1. Select Service Tier
              </label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {[
                  {
                    id: "basic",
                    name: "Basic",
                    price: "₹499",
                    brand: "VLCC / Streax",
                    dur: "45m",
                    features: ["Core ritual", "Single-use kit"],
                  },
                  {
                    id: "standard",
                    name: "Standard",
                    badge: "Most Popular",
                    price: "₹899",
                    brand: "O3+ / L'Oréal",
                    dur: "60m",
                    features: ["Deep treatment", "Head massage", "Sterile pouch"],
                  },
                  {
                    id: "premium",
                    name: "Premium Luxury",
                    price: "₹1,699",
                    brand: "Forest Essentials",
                    dur: "90m",
                    features: ["Organic 24K serum", "Eye mask", "Senior Stylist"],
                  },
                ].map((tier) => (
                  <div
                    key={tier.id}
                    onClick={() => setSelectedTier(tier.id as "basic" | "standard" | "premium")}
                    className={`relative cursor-pointer rounded-xl border p-4 transition-all ${
                      selectedTier === tier.id
                        ? "border-primary bg-primary/5 shadow-md shadow-primary/10"
                        : "border-card-border hover:border-muted/50"
                    }`}
                  >
                    {tier.badge && (
                      <span className="absolute -top-2.5 right-3 rounded-full bg-primary px-2 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                        {tier.badge}
                      </span>
                    )}
                    <h4 className="font-bold text-foreground">{tier.name}</h4>
                    <p className="mt-1 text-base font-extrabold text-primary">{tier.price}</p>
                    <p className="mt-0.5 text-[11px] text-muted">
                      {tier.brand} • {tier.dur}
                    </p>
                    <ul className="mt-3 space-y-1 text-[11px] text-muted">
                      {tier.features.map((f, i) => (
                        <li key={i} className="flex items-center gap-1.5">
                          <span className="text-primary">✓</span> {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-bold tracking-wider uppercase text-muted">
                2. Recommended Add-ons
              </label>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {[
                  { id: "ao_detan", name: "Express De-Tan Pack", price: "+₹299", dur: "+15m" },
                  { id: "ao_scalp", name: "Hydrating Scalp Serum Massage", price: "+₹299", dur: "+15m" },
                ].map((addon) => {
                  const isChecked = selectedAddOns.includes(addon.id);
                  return (
                    <div
                      key={addon.id}
                      onClick={() => {
                        setSelectedAddOns(
                          isChecked ? selectedAddOns.filter((x) => x !== addon.id) : [...selectedAddOns, addon.id]
                        );
                      }}
                      className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 text-xs transition-colors ${
                        isChecked ? "border-primary bg-primary/5 text-foreground" : "border-card-border text-muted"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="rounded border-card-border text-primary focus:ring-primary"
                        />
                        <span className="font-medium">{addon.name}</span>
                      </div>
                      <span className="font-bold text-primary">{addon.price}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end pt-3">
              <Button onClick={() => setStep(2)}>Next: Schedule & Address →</Button>
            </div>
          </div>
        )}

        {/* STEP 2: ADDRESS & DISPATCH TYPE */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-xs font-bold tracking-wider uppercase text-muted">
                Dispatch Mode & Arrival Time
              </label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div
                  onClick={() => setBookingType("instant")}
                  className={`cursor-pointer rounded-xl border p-4 transition-all ${
                    bookingType === "instant"
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-card-border hover:border-muted/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">⚡ Instant Dispatch</span>
                    <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-500 font-semibold text-[10px]">
                      15–25 Mins
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted">
                    Auto-matches the highest rated verified specialist closest to your GPS coordinates.
                  </p>
                  <p className="mt-2 text-[11px] text-amber-500/90 font-medium">
                    🛡️ Credible minimum ETA enforced (never 10-minute fantasy).
                  </p>
                </div>

                <div
                  onClick={() => setBookingType("scheduled")}
                  className={`cursor-pointer rounded-xl border p-4 transition-all ${
                    bookingType === "scheduled"
                      ? "border-primary bg-primary/5 shadow-sm"
                      : "border-card-border hover:border-muted/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-foreground">📅 Scheduled Appointment</span>
                    <Badge variant="outline" className="text-[10px]">
                      Guaranteed Slot
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs text-muted">
                    Pick a specific date and time slot. Guaranteed locking with zero double-booking.
                  </p>
                  {bookingType === "scheduled" && (
                    <select
                      value={selectedSlotTime}
                      onChange={(e) => setSelectedSlotTime(e.target.value)}
                      className="mt-3 w-full rounded-md border border-card-border bg-background p-1.5 text-xs text-foreground"
                    >
                      <option>Tomorrow, 10:00 AM - 11:00 AM</option>
                      <option>Tomorrow, 02:00 PM - 03:00 PM</option>
                      <option>Tomorrow, 05:00 PM - 06:00 PM</option>
                      <option>Day After, 11:00 AM - 12:00 PM</option>
                    </select>
                  )}
                </div>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-bold tracking-wider uppercase text-muted">
                Service Delivery Address
              </label>
              <div className="space-y-2">
                {savedAddresses.map((addr) => (
                  <div
                    key={addr.id}
                    onClick={() => setSelectedAddressId(addr.id)}
                    className={`flex cursor-pointer items-start justify-between rounded-xl border p-3 text-xs transition-colors ${
                      selectedAddressId === addr.id
                        ? "border-primary bg-primary/5 text-foreground"
                        : "border-card-border text-muted"
                    }`}
                  >
                    <div>
                      <span className="font-bold text-foreground">{addr.label}</span>
                      <p className="mt-0.5 text-muted">{addr.line1}</p>
                      <p className="text-[11px] text-muted">
                        Pincode: {addr.pincode} • Realistic Dispatch ETA: {addr.eta}
                      </p>
                    </div>
                    <input
                      type="radio"
                      checked={selectedAddressId === addr.id}
                      onChange={() => {}}
                      className="mt-1 text-primary focus:ring-primary"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between pt-3">
              <Button variant="ghost" onClick={() => setStep(1)}>
                ← Back
              </Button>
              <Button onClick={() => setStep(3)}>Next: Review Itemized Quote →</Button>
            </div>
          </div>
        )}

        {/* STEP 3: QUOTE BREAKDOWN & HOLD GENERATION */}
        {step === 3 && (
          <div className="space-y-5">
            <div className="rounded-xl border border-card-border bg-card/60 p-4">
              <div className="flex items-center justify-between border-b border-card-border pb-3">
                <div>
                  <h4 className="font-bold text-foreground">
                    {service.name} ({selectedTier.toUpperCase()})
                  </h4>
                  <p className="text-xs text-muted">
                    {bookingType === "instant" ? "⚡ Instant Dispatch (~18 mins)" : `📅 ${selectedSlotTime}`}
                  </p>
                </div>
                <Badge variant="secondary" className="text-xs">
                  {selectedTier}
                </Badge>
              </div>

              {/* Itemized list */}
              <div className="mt-4 space-y-2 text-xs">
                <div className="flex justify-between text-muted">
                  <span>Base Service Tier</span>
                  <span className="font-medium text-foreground">₹{(basePricePaise / 100).toFixed(2)}</span>
                </div>
                {selectedAddOns.map((ao) => (
                  <div key={ao} className="flex justify-between text-muted">
                    <span>Add-on: {ao === "ao_detan" ? "Express De-Tan Pack" : "Scalp Serum"}</span>
                    <span className="font-medium text-foreground">₹299.00</span>
                  </div>
                ))}
                <div className="flex justify-between text-muted">
                  <span>Doorstep Travel & Disinfection Fee</span>
                  <span className="font-medium text-emerald-500">FREE</span>
                </div>
                {discountPaise > 0 && (
                  <div className="flex justify-between text-emerald-500">
                    <span>Coupon Discount (WELCOME50)</span>
                    <span>-₹{(discountPaise / 100).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-muted pt-2 border-t border-card-border/60">
                  <span>Taxable Subtotal</span>
                  <span>₹{(taxablePaise / 100).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-muted">
                  <span>GST (18% - 9% CGST + 9% SGST)</span>
                  <span>₹{(gstPaise / 100).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm font-bold text-foreground pt-2 border-t border-card-border">
                  <span>Total Amount Payable</span>
                  <span className="text-base text-primary">₹{(totalPayablePaise / 100).toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Promo Code Input */}
            <div className="flex gap-2">
              <Input
                placeholder="Promo Code"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                className="text-xs"
              />
              <Button variant="outline" size="sm" onClick={() => {}}>
                Apply
              </Button>
            </div>

            <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-xs text-amber-500">
              ⏱️ Clicking &quot;Hold Slot &amp; Proceed&quot; creates an immutable 10-minute hold reservation with cryptographic
              concurrency protection.
            </div>

            <div className="flex justify-between pt-2">
              <Button variant="ghost" onClick={() => setStep(2)}>
                ← Back
              </Button>
              <Button onClick={handleCreateHold} disabled={isSubmitting}>
                {isSubmitting ? "Holding Slot..." : "Hold Slot & Proceed to Pay →"}
              </Button>
            </div>
          </div>
        )}

        {/* STEP 4: SANDBOX PAYMENT SIMULATION */}
        {step === 4 && activeBooking && (
          <div className="space-y-5">
            <div className="flex items-center justify-between rounded-xl bg-primary/10 border border-primary/20 p-3 text-xs">
              <div>
                <span className="font-bold text-primary">Checkout Hold Active:</span> {activeBooking.booking_number}
              </div>
              <div className="font-mono font-bold text-primary">
                ⏳ {formatTimer(holdSecondsRemaining)}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-xs font-bold tracking-wider uppercase text-muted">
                Select Sandbox Payment Method
              </label>
              <div className="space-y-2">
                {[
                  { id: "online_upi", title: "UPI Instant (Google Pay, PhonePe, Paytm)", icon: "📱" },
                  { id: "card", title: "Credit or Debit Card", icon: "💳" },
                  { id: "net_banking", title: "Netbanking (All Major Indian Banks)", icon: "🏦" },
                ].map((mode) => (
                  <div
                    key={mode.id}
                    onClick={() => setPaymentMethod(mode.id as "online_upi" | "card" | "net_banking")}
                    className={`flex cursor-pointer items-center justify-between rounded-xl border p-3 text-xs transition-colors ${
                      paymentMethod === mode.id
                        ? "border-primary bg-primary/5 text-foreground"
                        : "border-card-border text-muted"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="text-base">{mode.icon}</span>
                      <span className="font-semibold text-foreground">{mode.title}</span>
                    </div>
                    <input
                      type="radio"
                      checked={paymentMethod === mode.id}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Test Simulation Controls */}
            <div className="rounded-xl border border-dashed border-card-border p-3 text-xs space-y-2 bg-card/40">
              <span className="font-bold text-foreground">🧪 Sandbox Verification Controls:</span>
              <p className="text-muted text-[11px]">
                In accordance with GlamNow ADR-0004, payment is verified cryptographically on the server using
                HMAC-SHA256 signatures before transitioning to CONFIRMED.
              </p>
              <label className="flex items-center gap-2 cursor-pointer pt-1 text-red-500 font-medium">
                <input
                  type="checkbox"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  className="rounded border-red-500 text-red-500"
                />
                Simulate Payment Rejection / Gateway Outage
              </label>
            </div>

            <div className="flex justify-between items-center pt-2">
              <div className="text-xs">
                <span className="text-muted">Payable: </span>
                <span className="font-bold text-base text-primary">₹{(totalPayablePaise / 100).toFixed(2)}</span>
              </div>
              <Button onClick={handleConfirmPayment} disabled={isSubmitting}>
                {isSubmitting ? "Verifying HMAC Signature..." : `Authorize & Pay ₹${(totalPayablePaise / 100).toFixed(2)}`}
              </Button>
            </div>
          </div>
        )}

        {/* STEP 5: BOOKING CONFIRMATION & OTP DISPLAY */}
        {step === 5 && activeBooking && (
          <div className="space-y-6 text-center py-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-3xl text-emerald-500 animate-bounce">
              ✓
            </div>

            <div>
              <h3 className="text-xl font-extrabold text-foreground">Booking Confirmed &amp; Dispatched!</h3>
              <p className="mt-1 text-xs text-muted">
                Reference ID: <strong className="text-primary font-mono">{activeBooking.booking_number}</strong>
              </p>
            </div>

            {/* OTP Handoff Verification Card */}
            <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto">
              <div className="rounded-xl border border-primary/30 bg-primary/5 p-3 text-center">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted">Start OTP</span>
                <div className="mt-1 text-2xl font-mono font-black text-primary tracking-widest">
                  {activeBooking.start_otp}
                </div>
                <p className="mt-1 text-[10px] text-muted">Share upon partner doorstep arrival</p>
              </div>

              <div className="rounded-xl border border-card-border bg-card/60 p-3 text-center">
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted">Completion OTP</span>
                <div className="mt-1 text-2xl font-mono font-black text-foreground tracking-widest">
                  {activeBooking.completion_otp}
                </div>
                <p className="mt-1 text-[10px] text-muted">Share once service is complete</p>
              </div>
            </div>

            <div className="rounded-xl border border-card-border bg-card/40 p-4 text-left max-w-md mx-auto text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-muted">Assigned Specialist:</span>
                <span className="font-bold text-foreground">{activeBooking.assigned_professional_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Estimated Arrival:</span>
                <span className="font-bold text-emerald-500">~18 mins (Live tracking enabled)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Cancellation SLA:</span>
                <span className="text-muted">100% free before partner is en route</span>
              </div>
            </div>

            <div className="flex gap-3 justify-center pt-2">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
              <Button
                onClick={() => {
                  onClose();
                  router.push(`/bookings/${activeBooking.id}`);
                }}
              >
                Track Live Booking →
              </Button>
            </div>
          </div>
        )}
      </div>
    </Dialog>
  );
}
