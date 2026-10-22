/**
 * Typed Booking, Quick Dispatch and Payment API Client (Phase 6).
 */

import { api } from "@/lib/api/client";

export type BookingStatus =
  | "hold_reserved"
  | "confirmed"
  | "dispatching"
  | "assigned"
  | "en_route"
  | "arrived"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "failed_assignment"
  | "expired";

export type BookingType = "instant" | "scheduled";

export interface BookingPriceSnapshotDto {
  base_rate_paise: number;
  add_ons_total_paise: number;
  travel_fee_paise: number;
  discount_applied_paise: number;
  taxable_amount_paise: number;
  cgst_paise: number;
  sgst_paise: number;
  total_payable_paise: number;
  snapshot_hash: string;
}

export interface BookingItemDto {
  name: string;
  item_type: string;
  price_paise: number;
  quantity: number;
}

export interface BookingStatusHistoryDto {
  from_status: BookingStatus | null;
  to_status: BookingStatus;
  actor_role: string;
  reason: string | null;
  created_at: string;
}

export interface BookingDetailDto {
  id: string;
  booking_number: string;
  customer_id: string;
  assigned_professional_id: string | null;
  assigned_professional_name: string | null;
  service_id: string;
  service_name: string;
  tier_type: "basic" | "standard" | "premium";
  booking_type: BookingType;
  status: BookingStatus;
  address_snapshot: {
    address_line1: string;
    address_line2?: string;
    city: string;
    state: string;
    pincode: string;
    landmark?: string;
    latitude: number;
    longitude: number;
  };
  scheduled_start_time: string | null;
  scheduled_end_time: string | null;
  hold_expires_at: string;
  start_otp: string;
  completion_otp?: string;
  eta_minutes: number | null;
  is_fallback_location: boolean;
  cancellation_fee_paise: number;
  price_snapshot: BookingPriceSnapshotDto;
  items: BookingItemDto[];
  history: BookingStatusHistoryDto[];
}

export interface CreateBookingHoldInput {
  service_id: string;
  tier_type: "basic" | "standard" | "premium";
  booking_type: BookingType;
  address_id: string;
  preferred_professional_id?: string | null;
  slot_id?: string | null;
  add_on_ids?: string[];
  coupon_code?: string | null;
  idempotency_key: string;
}

export interface PaymentInitiateDto {
  booking_id: string;
  booking_number: string;
  gateway_order_id: string;
  amount_paise: number;
  currency: string;
  hold_expires_at: string;
}

export interface PaymentConfirmInput {
  gateway_order_id: string;
  gateway_payment_id: string;
  signature: string;
  payment_method: "online_upi" | "card" | "net_banking" | "cash_on_service";
  idempotency_key: string;
}

export interface PaymentConfirmDto {
  ok: boolean;
  booking_id: string;
  booking_status: BookingStatus;
  payment_status: string;
  message: string;
}

export const bookingApi = {
  async createHold(data: CreateBookingHoldInput): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>("/bookings", data);
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to create booking reservation hold");
    }
    return res.data;
  },

  async getBooking(id: string): Promise<BookingDetailDto> {
    const res = await api.get<BookingDetailDto>(`/bookings/${id}`);
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to fetch booking details");
    }
    return res.data;
  },

  async initiatePayment(bookingId: string): Promise<PaymentInitiateDto> {
    const res = await api.post<PaymentInitiateDto>(`/bookings/${bookingId}/pay`);
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to initiate payment");
    }
    return res.data;
  },

  async confirmPayment(bookingId: string, data: PaymentConfirmInput): Promise<PaymentConfirmDto> {
    const res = await api.post<PaymentConfirmDto>(`/bookings/${bookingId}/confirm-payment`, data);
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to confirm payment");
    }
    return res.data;
  },

  async respondToDispatch(
    bookingId: string,
    action: "accept" | "decline",
    declineReason?: string
  ): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/dispatch-response`, {
      action,
      decline_reason: declineReason,
    });
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to submit professional response");
    }
    return res.data;
  },

  async markArrived(bookingId: string): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/mark-arrived`);
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to mark arrival");
    }
    return res.data;
  },

  async verifyStartOtp(bookingId: string, otp: string): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/verify-start`, { otp });
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to verify start OTP");
    }
    return res.data;
  },

  async completeService(bookingId: string, otp: string): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/complete`, { otp });
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to complete service");
    }
    return res.data;
  },

  async cancelBooking(bookingId: string, reason: string): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/cancel`, { reason });
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to cancel booking");
    }
    return res.data;
  },

  async rescheduleBooking(bookingId: string, newSlotId: string): Promise<BookingDetailDto> {
    const res = await api.post<BookingDetailDto>(`/bookings/${bookingId}/reschedule`, {
      new_slot_id: newSlotId,
    });
    if (!res.ok || !res.data) {
      throw new Error(res.error || "Failed to reschedule booking");
    }
    return res.data;
  },
};
