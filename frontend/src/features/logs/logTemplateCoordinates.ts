/**
 * Centralized coordinate configuration for the daily-log SVG overlay.
 *
 * ALL pixel positions for the overlay live here (never scattered through the
 * component) so the template can be calibrated in one place. Coordinates are in
 * the SVG viewBox space, which matches the supplied blank-paper-log.png at its
 * native pixel size.
 *
 * The template image is 513 x 518 px. Values below are calibrated visually
 * against that image; the dev-only calibration grid (see DailyLogSheet) overlays
 * a ruler to fine-tune them.
 */
import type { DutyStatus } from "../../types/trip";

export const TEMPLATE = {
  src: "/assets/blank-paper-log.png",
  width: 513,
  height: 518,
} as const;

/**
 * Duty-status graph grid.
 *
 * Values are calibrated from the template's pixels: the 24-hour band spans
 * x=80..470 (24 uniform ~16.25px hours; the printed 23:00 line is at x=454) and
 * the four status rows are separated by horizontal lines at
 * y=182/201/218/235/253. Verified by compositing the graph over the template.
 */
export const GRID = {
  // X of the "Midnight" start line and the ending "Midnight" line.
  startX: 80,
  endX: 470,
  // Y center of each of the four status rows (top to bottom on the sheet).
  rowY: {
    OFF_DUTY: 191,
    SLEEPER_BERTH: 209,
    DRIVING: 226,
    ON_DUTY_NOT_DRIVING: 244,
  } as Record<DutyStatus, number>,
  // Top/bottom of the whole grid band (for the calibration overlay).
  top: 182,
  bottom: 253,
  // X for the per-row daily totals in the "Total Hours" column.
  totalsX: 490,
} as const;

/** Header/identity text fields. */
export const FIELDS = {
  dateMonth: { x: 300, y: 20 },
  dateDay: { x: 344, y: 20 },
  dateYear: { x: 392, y: 20 },
  from: { x: 92, y: 43 },
  to: { x: 278, y: 55 },
  totalMilesDriving: { x: 62, y: 86 },
  totalMileage: { x: 165, y: 86 },
  carrier: { x: 300, y: 88 },
  mainOffice: { x: 300, y: 106 },
  truckTrailer: { x: 60, y: 123 },
  homeTerminal: { x: 300, y: 123 },
  driverName: { x: 92, y: 33 },
} as const;

export const REMARKS = {
  x: 46,
  startY: 292,
  lineHeight: 9,
  maxLines: 10,
  fontSize: 6.5,
} as const;

export const SHIPPING = {
  documents: { x: 95, y: 332 },
} as const;

/** Recap (bottom section) — modeled 70-hour values. */
export const RECAP = {
  onDutyToday: { x: 118, y: 452 },
  availableTomorrow: { x: 300, y: 470 },
} as const;

/**
 * Convert minutes-from-midnight (0..1440) to an X coordinate on the grid.
 *
 *   x = startX + (minutes / 1440) * (endX - startX)
 */
export function minuteToX(minutesFromMidnight: number): number {
  const clamped = Math.max(0, Math.min(1440, minutesFromMidnight));
  return GRID.startX + (clamped / 1440) * (GRID.endX - GRID.startX);
}

export function rowYFor(duty: DutyStatus): number {
  return GRID.rowY[duty];
}
