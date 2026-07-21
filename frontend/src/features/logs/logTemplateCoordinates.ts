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

/**
 * Header/identity text fields — calibrated from the template's fill-in lines:
 * date blanks at y=19 (centers x=187/229/271), From/To lines at y=47, the two
 * mileage boxes, and the carrier/office/terminal lines at y=79/99/120.
 */
export const FIELDS = {
  dateMonth: { x: 187, y: 17 },
  dateDay: { x: 229, y: 17 },
  dateYear: { x: 271, y: 17 },
  from: { x: 95, y: 45 },
  to: { x: 278, y: 45 },
  totalMilesDriving: { x: 66, y: 80 },
  totalMileage: { x: 150, y: 80 },
  carrier: { x: 347, y: 77 },
  mainOffice: { x: 347, y: 97 },
  truckTrailer: { x: 56, y: 112 },
  homeTerminal: { x: 347, y: 118 },
  driverName: { x: 130, y: 36 },
} as const;

export const REMARKS = {
  x: 150,
  startY: 300,
  lineHeight: 11,
  maxLines: 8,
  fontSize: 6.5,
} as const;

export const SHIPPING = {
  documents: { x: 48, y: 351 },
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
