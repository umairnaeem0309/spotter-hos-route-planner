import type { DailyLog, DutyStatus } from "../../types/trip";
import { formatDate } from "../../lib/format";
import {
  FIELDS,
  GRID,
  RECAP,
  REMARKS,
  SHIPPING,
  TEMPLATE,
  minuteToX,
  rowYFor,
} from "./logTemplateCoordinates";

interface DailyLogSheetProps {
  log: DailyLog;
  /** Dev-only: overlay a coordinate ruler to calibrate the template. */
  showCalibration?: boolean;
}

const DUTY_ORDER: DutyStatus[] = [
  "OFF_DUTY",
  "SLEEPER_BERTH",
  "DRIVING",
  "ON_DUTY_NOT_DRIVING",
];

function hoursMinutes(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}:${String(m).padStart(2, "0")}`;
}

function graphPoints(log: DailyLog): string {
  // A continuous polyline: horizontal along each status row, with implicit
  // vertical connectors where consecutive segments change rows.
  const pts: string[] = [];
  for (const seg of log.segments) {
    const y = rowYFor(seg.duty_status);
    pts.push(`${minuteToX(seg.start_minute).toFixed(1)},${y}`);
    pts.push(`${minuteToX(seg.end_minute).toFixed(1)},${y}`);
  }
  return pts.join(" ");
}

export function DailyLogSheet({ log, showCalibration = false }: DailyLogSheetProps) {
  const [year, month, day] = log.date.split("-");
  const meta = log.metadata;

  return (
    <svg
      viewBox={`0 0 ${TEMPLATE.width} ${TEMPLATE.height}`}
      className="h-auto w-full"
      role="img"
      aria-label={`Driver daily log for ${formatDate(log.date)}`}
      style={{ fontFamily: "Arial, sans-serif" }}
    >
      <image
        href={TEMPLATE.src}
        x={0}
        y={0}
        width={TEMPLATE.width}
        height={TEMPLATE.height}
      />

      {/* Identity / header fields */}
      <g fill="#111827" fontSize={7}>
        <text x={FIELDS.dateMonth.x} y={FIELDS.dateMonth.y} textAnchor="middle">
          {month}
        </text>
        <text x={FIELDS.dateDay.x} y={FIELDS.dateDay.y} textAnchor="middle">
          {day}
        </text>
        <text x={FIELDS.dateYear.x} y={FIELDS.dateYear.y} textAnchor="middle">
          {year}
        </text>
        <text x={FIELDS.driverName.x} y={FIELDS.driverName.y} fontSize={6.5} fill="#6b7280">
          Driver: {meta.driver_name} (demo)
        </text>
        <text x={FIELDS.from.x} y={FIELDS.from.y}>{log.from_label}</text>
        <text x={FIELDS.to.x} y={FIELDS.to.y}>{log.to_label}</text>
        <text x={FIELDS.totalMilesDriving.x} y={FIELDS.totalMilesDriving.y}>
          {Math.round(log.total_miles)}
        </text>
        <text x={FIELDS.totalMileage.x} y={FIELDS.totalMileage.y}>
          {Math.round(log.total_miles)}
        </text>
        <text x={FIELDS.carrier.x} y={FIELDS.carrier.y} textAnchor="middle">
          {meta.carrier}
        </text>
        <text x={FIELDS.mainOffice.x} y={FIELDS.mainOffice.y} textAnchor="middle">
          {meta.main_office}
        </text>
        <text x={FIELDS.truckTrailer.x} y={FIELDS.truckTrailer.y} fontSize={6}>
          {meta.vehicle}
        </text>
        <text x={FIELDS.homeTerminal.x} y={FIELDS.homeTerminal.y} textAnchor="middle">
          {meta.main_office}
        </text>
      </g>

      {/* Duty-status graph */}
      <polyline
        points={graphPoints(log)}
        fill="none"
        stroke="#0d3b66"
        strokeWidth={1.6}
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {/* Per-row daily totals in the Total Hours column */}
      <g fill="#111827" fontSize={7} textAnchor="middle">
        {DUTY_ORDER.map((duty) => (
          <text key={duty} x={GRID.totalsX} y={rowYFor(duty) + 2}>
            {hoursMinutes(log.totals[duty])}
          </text>
        ))}
      </g>

      {/* Shipping document */}
      <text x={SHIPPING.documents.x} y={SHIPPING.documents.y} fontSize={6.5} fill="#111827">
        {meta.shipping_document} (demo)
      </text>

      {/* Remarks */}
      <g fill="#111827" fontSize={REMARKS.fontSize}>
        {log.remarks.slice(0, REMARKS.maxLines).map((r, i) => (
          <text key={i} x={REMARKS.x} y={REMARKS.startY + i * REMARKS.lineHeight}>
            {r.time} — {r.location} — {r.activity}
          </text>
        ))}
      </g>

      {/* Modeled recap */}
      <g fill="#111827" fontSize={6.5}>
        <text x={RECAP.onDutyToday.x} y={RECAP.onDutyToday.y}>
          {hoursMinutes(log.recap.on_duty_minutes_today)}
        </text>
        <text x={RECAP.availableTomorrow.x} y={RECAP.availableTomorrow.y}>
          {log.recap.cycle_hours_available.toFixed(1)} h available
        </text>
      </g>

      {showCalibration && <CalibrationGrid />}
    </svg>
  );
}

/** Dev-only ruler: hour verticals + status-row guides to align coordinates. */
function CalibrationGrid() {
  const hours = Array.from({ length: 25 }, (_, i) => i);
  return (
    <g pointerEvents="none">
      {hours.map((h) => {
        const x = minuteToX(h * 60);
        return (
          <g key={h}>
            <line x1={x} y1={GRID.top} x2={x} y2={GRID.bottom} stroke="#ef4444" strokeWidth={0.3} />
            <text x={x} y={GRID.top - 2} fontSize={4} fill="#ef4444" textAnchor="middle">
              {h}
            </text>
          </g>
        );
      })}
      {DUTY_ORDER.map((duty) => (
        <line
          key={duty}
          x1={GRID.startX}
          y1={rowYFor(duty)}
          x2={GRID.endX}
          y2={rowYFor(duty)}
          stroke="#22c55e"
          strokeWidth={0.3}
        />
      ))}
    </g>
  );
}
