"use client";

import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";

export interface SlotItem {
  id: string;
  professionalId: string;
  startTime: string; // ISO
  endTime: string;   // ISO
  status: "available" | "reserved" | "booked" | "blocked";
  reservationExpiresAt?: string | null;
}

export interface DayItem {
  dateObj: Date;
  dateString: string;
  dayName: string;
  formattedDate: string;
}

export interface SlotSelectorProps {
  professionalId: string;
  professionalName: string;
  onSlotReserved?: (slot: SlotItem) => void;
}

function getInitialDays(): DayItem[] {
  const base = typeof window === "undefined" ? new Date("2026-10-22T00:00:00Z") : new Date();
  return Array.from({ length: 5 }, (_, i) => {
    const d = new Date(base);
    d.setDate(base.getDate() + i);
    return {
      dateObj: d,
      dateString: d.toISOString().split("T")[0],
      dayName: i === 0 ? "Today" : i === 1 ? "Tomorrow" : d.toLocaleDateString("en-IN", { weekday: "short" }),
      formattedDate: d.toLocaleDateString("en-IN", { month: "short", day: "numeric" }),
    };
  });
}

export function SlotSelector({
  professionalId,
  professionalName,
  onSlotReserved,
}: SlotSelectorProps) {
  const [days] = useState<DayItem[]>(getInitialDays);
  const [selectedDate, setSelectedDate] = useState<string>(() => days[0]?.dateString ?? "");
  const [selectedSlot, setSelectedSlot] = useState<SlotItem | null>(null);
  const [isHolding, setIsHolding] = useState(false);
  const [heldSlot, setHeldSlot] = useState<SlotItem | null>(null);
  const [holdSecondsLeft, setHoldSecondsLeft] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Compute slots cleanly using useMemo without cascading render setState effects
  const slots = useMemo<SlotItem[]>(() => {
    if (!selectedDate || days.length === 0) return [];
    const baseDate = new Date(selectedDate);
    return [
      { h: 9, m: 0 },
      { h: 10, m: 30 },
      { h: 12, m: 0 },
      { h: 13, m: 0, break: true }, // Lunch break
      { h: 14, m: 30 },
      { h: 16, m: 0 },
      { h: 17, m: 30 },
    ].map((timeSpec, idx) => {
      const s = new Date(baseDate);
      s.setHours(timeSpec.h, timeSpec.m, 0, 0);
      const e = new Date(s);
      e.setMinutes(s.getMinutes() + 60);

      let status: "available" | "reserved" | "booked" | "blocked" = "available";
      if (timeSpec.break) {
        status = "blocked";
      } else if (idx === 1 && selectedDate === days[0].dateString) {
        status = "booked";
      }

      return {
        id: `slot_${selectedDate}_${timeSpec.h}_${timeSpec.m}`,
        professionalId,
        startTime: s.toISOString(),
        endTime: e.toISOString(),
        status,
      };
    });
  }, [selectedDate, professionalId, days]);

  // Hold countdown timer
  useEffect(() => {
    if (!heldSlot) return;
    const timer = setInterval(() => {
      setHoldSecondsLeft((prev) => {
        if (prev <= 1) {
          setHeldSlot(null);
          setErrorMessage("Slot hold expired. Please select a time slot again.");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [heldSlot]);

  const handleSelectSlot = (slot: SlotItem) => {
    setErrorMessage(null);
    if (slot.status === "booked") {
      setErrorMessage("This slot is already booked by another client. Please pick another available time.");
      return;
    }
    if (slot.status === "blocked") {
      setErrorMessage("This time window is unavailable due to working schedule or partner lunch break.");
      return;
    }
    if (slot.status === "reserved" && heldSlot?.id !== slot.id) {
      setErrorMessage("This appointment slot is currently being held during checkout by another customer.");
      return;
    }
    setSelectedSlot(slot);
  };

  const handleHoldSlot = () => {
    if (!selectedSlot) return;
    setIsHolding(true);
    // Simulate atomic reservation call
    setTimeout(() => {
      setIsHolding(false);
      const reserved = { ...selectedSlot, status: "reserved" as const };
      setHeldSlot(reserved);
      setHoldSecondsLeft(15 * 60); // 15 mins lock window
      onSlotReserved?.(reserved);
    }, 400);
  };

  const handleReleaseSlot = () => {
    setHeldSlot(null);
    setSelectedSlot(null);
    setHoldSecondsLeft(0);
    setErrorMessage(null);
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  if (!selectedDate || days.length === 0) {
    return (
      <div className="p-8 rounded-gn-lg border border-gn-border-default bg-gn-bg-card animate-pulse text-xs text-gn-text-tertiary text-center">
        Loading live appointment schedule...
      </div>
    );
  }

  return (
    <div className="space-y-5 rounded-gn-lg border border-gn-border-default bg-gn-bg-card p-5 shadow-gn-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gn-border-default/80 pb-4">
        <div>
          <h3 className="font-serif text-lg font-bold text-gn-text-primary">
            Book Appointment Slot
          </h3>
          <p className="text-xs text-gn-text-tertiary">
            Real-time verified availability for {professionalName}
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-gn-text-secondary">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Available
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Reserved / Hold
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-red-400" /> Booked
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-slate-300" /> Break / Off
          </span>
        </div>
      </div>

      {/* Date Picker Ribbon */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {days.map((d) => {
          const isSelected = selectedDate === d.dateString;
          return (
            <button
              key={d.dateString}
              onClick={() => {
                setSelectedDate(d.dateString);
                setSelectedSlot(null);
                setErrorMessage(null);
              }}
              className={`
                flex flex-col items-center justify-center min-w-[76px] py-2.5 px-3 rounded-gn-md border text-center transition-all cursor-pointer gn-focus-ring
                ${isSelected
                  ? "bg-gn-accent-primary text-white border-gn-accent-primary shadow-gn-sm font-semibold"
                  : "bg-gn-bg-secondary/70 border-gn-border-default text-gn-text-secondary hover:bg-gn-bg-secondary"
                }
              `}
            >
              <span className="text-[11px] uppercase tracking-wider">{d.dayName}</span>
              <span className="text-sm font-bold mt-0.5">{d.formattedDate}</span>
            </button>
          );
        })}
      </div>

      {/* Slots Grid */}
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-gn-text-tertiary">
          Available Time Windows
        </span>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
          {slots.map((slot) => {
            const timeStr = new Date(slot.startTime).toLocaleTimeString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
              hour12: true,
            });

            const isSelected = selectedSlot?.id === slot.id || heldSlot?.id === slot.id;
            const isHeldByMe = heldSlot?.id === slot.id;

            return (
              <button
                key={slot.id}
                onClick={() => handleSelectSlot(slot)}
                disabled={slot.status === "booked" || slot.status === "blocked"}
                className={`
                  p-3 rounded-gn-md border text-left transition-all relative flex flex-col justify-between h-20 gn-focus-ring
                  ${slot.status === "booked"
                    ? "bg-red-50/50 border-red-200 text-red-400 cursor-not-allowed line-through"
                    : slot.status === "blocked"
                    ? "bg-slate-100/60 border-slate-200 text-slate-400 cursor-not-allowed"
                    : isHeldByMe
                    ? "bg-amber-50 border-amber-500 ring-2 ring-amber-400 text-amber-900"
                    : isSelected
                    ? "bg-gn-accent-primary-subtle border-gn-accent-primary ring-2 ring-gn-accent-primary text-gn-text-primary"
                    : "bg-gn-bg-secondary/40 border-gn-border-default hover:border-gn-border-strong text-gn-text-primary cursor-pointer"
                  }
                `}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-xs font-bold">{timeStr}</span>
                  {slot.status === "available" && (
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  )}
                  {slot.status === "booked" && (
                    <span className="text-[9px] font-bold text-red-500 uppercase">Booked</span>
                  )}
                  {slot.status === "blocked" && (
                    <span className="text-[9px] text-slate-400 font-medium">Break</span>
                  )}
                  {slot.status === "reserved" && !isHeldByMe && (
                    <span className="text-[9px] text-amber-600 font-semibold">On Hold</span>
                  )}
                  {isHeldByMe && (
                    <span className="text-[9px] bg-amber-200 text-amber-900 px-1 rounded font-bold">
                      Held
                    </span>
                  )}
                </div>

                <span className="text-[10px] text-gn-text-tertiary">
                  60 min service window
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error or Alert banner */}
      {errorMessage && (
        <div className="p-3 rounded-gn-md bg-red-50 border border-red-200 text-xs text-red-700 flex items-center justify-between gn-fade-in">
          <span>⚠️ {errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 font-bold ml-2">×</button>
        </div>
      )}

      {/* Reservation Hold Active Bar */}
      {heldSlot ? (
        <div className="p-4 rounded-gn-md bg-amber-50/80 border border-amber-300 flex flex-col sm:flex-row sm:items-center justify-between gap-3 gn-fade-in">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-amber-500 gn-pulse" />
              <span className="text-xs font-bold text-amber-900">
                Slot Reserved Exclusively For You
              </span>
            </div>
            <p className="text-xs text-amber-800 mt-0.5">
              Time locked for <strong>{formatTimer(holdSecondsLeft)}</strong>. Complete checkout to confirm.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleReleaseSlot} className="text-xs text-amber-800">
              Release Slot
            </Button>
            <Button variant="primary" size="sm" className="bg-amber-600 hover:bg-amber-700 text-white text-xs">
              Proceed with Slot ✓
            </Button>
          </div>
        </div>
      ) : (
        selectedSlot && (
          <div className="pt-2 flex items-center justify-between border-t border-gn-border-default/60">
            <span className="text-xs text-gn-text-secondary">
              Selected: <strong>{new Date(selectedSlot.startTime).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</strong>
            </span>
            <Button
              variant="primary"
              size="sm"
              onClick={handleHoldSlot}
              disabled={isHolding}
            >
              {isHolding ? "Locking Slot..." : "Reserve Slot (15 min hold)"}
            </Button>
          </div>
        )
      )}
    </div>
  );
}
