import type { TimelineEvent } from "../../types/trip";
import { Section } from "../../components/ui/Card";
import {
  EVENT_DISPLAY,
  REASON_TEXT,
  formatDuration,
  formatTime,
} from "../../lib/format";

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events }: TimelineProps) {
  return (
    <Section
      title="HOS-compliant schedule"
      subtitle="Chronological driving, stops, breaks, and rest"
    >
      <ol className="relative space-y-3">
        {events.map((event, index) => {
          const display = EVENT_DISPLAY[event.type];
          const reason = event.reason_code
            ? REASON_TEXT[event.reason_code]
            : undefined;
          return (
            <li
              key={index}
              className="flex gap-3 rounded-lg border border-slate-100 bg-slate-50/60 p-3"
            >
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-lg"
                style={{ backgroundColor: `${display.color}1a` }}
                aria-hidden
              >
                {display.icon}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <span className="font-semibold text-navy-800">
                    {display.label}
                  </span>
                  <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${display.chip}`}>
                    {formatDuration(event.duration_minutes)}
                  </span>
                  {event.distance_miles > 0 && (
                    <span className="text-xs text-slate-500">
                      {event.distance_miles.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}{" "}
                      mi
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-sm text-slate-600">
                  {formatTime(event.start_at)} – {formatTime(event.end_at)}
                  {event.location_label && (
                    <>
                      {" · "}
                      <span className="font-medium text-slate-700">
                        {event.location_label}
                      </span>
                    </>
                  )}
                </p>
                {reason && (
                  <p className="mt-1 text-xs italic text-slate-500">{reason}</p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </Section>
  );
}
