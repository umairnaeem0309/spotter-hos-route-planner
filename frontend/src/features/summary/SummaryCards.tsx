import type { TripSummary } from "../../types/trip";
import { Card } from "../../components/ui/Card";
import { formatDateTime, formatDuration } from "../../lib/format";

interface SummaryCardsProps {
  summary: TripSummary;
}

interface Metric {
  label: string;
  value: string;
  hint?: string;
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  const metrics: Metric[] = [
    {
      label: "Total distance",
      value: `${summary.total_distance_miles.toLocaleString(undefined, { maximumFractionDigits: 0 })} mi`,
    },
    {
      label: "Raw driving time",
      value: formatDuration(summary.raw_driving_minutes),
      hint: "Provider estimate, before stops",
    },
    {
      label: "Compliant duration",
      value: formatDuration(summary.compliant_trip_minutes),
      hint: "Including breaks, fuel & rest",
    },
    {
      label: "Log days",
      value: String(summary.number_of_log_days),
    },
  ];

  const badges: Metric[] = [
    { label: "Departure", value: formatDateTime(summary.departure_at) },
    { label: "Arrival", value: formatDateTime(summary.arrival_at) },
  ];

  const counts = [
    { label: "Fuel stops", value: summary.fuel_stop_count, dot: "#d97706" },
    { label: "30-min breaks", value: summary.rest_break_count, dot: "#64748b" },
    { label: "Sleeper rests", value: summary.overnight_rest_count, dot: "#4f46e5" },
    { label: "34-hr restarts", value: summary.cycle_restart_count, dot: "#e11d48" },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {metrics.map((m) => (
          <Card
            key={m.label}
            className="p-4 transition duration-200 hover:-translate-y-0.5 hover:shadow-md"
          >
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {m.label}
            </p>
            <p className="mt-1 text-2xl font-bold text-navy-800">{m.value}</p>
            {m.hint && <p className="mt-0.5 text-xs text-slate-400">{m.hint}</p>}
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {badges.map((b) => (
          <Card key={b.label} className="flex items-center justify-between p-4">
            <span className="text-sm font-medium text-slate-500">{b.label}</span>
            <span className="text-sm font-semibold text-navy-800">{b.value}</span>
          </Card>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {counts.map((c) => (
          <span
            key={c.label}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600"
          >
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: c.dot }}
            />
            {c.label}
            <span className="ml-0.5 rounded-full bg-slate-100 px-1.5 font-semibold text-slate-700">
              {c.value}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
