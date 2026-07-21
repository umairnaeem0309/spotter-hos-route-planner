import type { DutyStatus, EventType } from "../types/trip";

/** "8h 30m" from minutes. */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatMiles(miles: number): string {
  return `${miles.toLocaleString(undefined, { maximumFractionDigits: 0 })} mi`;
}

/** Format an ISO datetime in its own offset (the trip timezone). */
export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(iso: string): string {
  // iso may be a date-only "YYYY-MM-DD"; append time to avoid tz shifting.
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  return d.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export interface EventDisplay {
  label: string;
  /** Tailwind classes for a colored chip. */
  chip: string;
  /** Hex color for map markers / graph. */
  color: string;
  /** Single-character glyph for compact map markers. */
  glyph: string;
}

export const EVENT_DISPLAY: Record<EventType, EventDisplay> = {
  driving: { label: "Driving", chip: "bg-teal-100 text-teal-800", color: "#0d9488", glyph: "▶" },
  pickup: { label: "Pickup", chip: "bg-emerald-100 text-emerald-800", color: "#059669", glyph: "P" },
  dropoff: { label: "Drop-off", chip: "bg-blue-100 text-blue-800", color: "#2563eb", glyph: "D" },
  fuel: { label: "Fuel stop", chip: "bg-amber-100 text-amber-800", color: "#d97706", glyph: "F" },
  rest_break: { label: "30-min break", chip: "bg-slate-200 text-slate-700", color: "#64748b", glyph: "B" },
  sleeper_berth: { label: "Sleeper berth", chip: "bg-indigo-100 text-indigo-800", color: "#4f46e5", glyph: "S" },
  cycle_restart: { label: "34-hour restart", chip: "bg-rose-100 text-rose-800", color: "#e11d48", glyph: "R" },
};

export const DUTY_STATUS_LABEL: Record<DutyStatus, string> = {
  OFF_DUTY: "Off Duty",
  SLEEPER_BERTH: "Sleeper Berth",
  DRIVING: "Driving",
  ON_DUTY_NOT_DRIVING: "On Duty (Not Driving)",
};

export const REASON_TEXT: Record<string, string> = {
  ELEVEN_HOUR_LIMIT:
    "Ten-hour sleeper period scheduled because the driver reached the 11-hour driving limit.",
  FOURTEEN_HOUR_WINDOW:
    "Ten-hour sleeper period scheduled because the 14-hour driving window elapsed.",
  EIGHT_HOUR_BREAK:
    "30-minute rest scheduled because the driver reached eight cumulative driving hours.",
  FUEL_INTERVAL:
    "Fuel stop scheduled at the ~900-mile planning interval (also satisfies the 30-minute break).",
  CYCLE_EXHAUSTED:
    "34-hour restart scheduled because the modeled 70-hour cycle was exhausted.",
  PICKUP: "Pickup — 60 minutes On Duty (Not Driving).",
  DROPOFF: "Drop-off — 60 minutes On Duty (Not Driving).",
};
