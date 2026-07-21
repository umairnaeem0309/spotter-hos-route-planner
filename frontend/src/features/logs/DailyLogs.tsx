import { useState } from "react";

import type { DailyLog } from "../../types/trip";
import { Section } from "../../components/ui/Card";
import { DUTY_STATUS_LABEL, formatDate } from "../../lib/format";
import { DailyLogSheet } from "./DailyLogSheet";

interface DailyLogsProps {
  logs: DailyLog[];
}

export function DailyLogs({ logs }: DailyLogsProps) {
  const [active, setActive] = useState(0);
  const [showCalibration, setShowCalibration] = useState(false);

  if (logs.length === 0) return null;
  const current = logs[Math.min(active, logs.length - 1)];
  const isDev = import.meta.env.DEV;

  const actions = (
    <div className="no-print flex items-center gap-2">
      {isDev && (
        <label className="flex items-center gap-1 text-xs text-slate-500">
          <input
            type="checkbox"
            checked={showCalibration}
            onChange={(e) => setShowCalibration(e.target.checked)}
          />
          Calibrate
        </label>
      )}
      <button
        type="button"
        onClick={() => window.print()}
        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-teal-400 hover:text-teal-700"
      >
        Print logs
      </button>
    </div>
  );

  return (
    <Section
      title="Driver daily logs"
      subtitle={`${logs.length} calendar ${logs.length === 1 ? "day" : "days"}`}
      actions={actions}
    >
      {/* Day tabs (screen only) */}
      {logs.length > 1 && (
        <div className="no-print mb-4 flex flex-wrap gap-2">
          {logs.map((log, i) => (
            <button
              key={log.date}
              type="button"
              onClick={() => setActive(i)}
              aria-current={i === active}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                i === active
                  ? "bg-navy-700 text-white"
                  : "border border-slate-300 bg-white text-slate-600 hover:border-teal-400"
              }`}
            >
              Day {i + 1}
              <span className="ml-1 hidden opacity-70 sm:inline">
                · {log.date}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Screen view: the active sheet. Print view: all sheets, one per page. */}
      <div className="no-print">
        <LogPanel log={current} showCalibration={showCalibration} />
        {logs.length > 1 && (
          <div className="mt-3 flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => setActive((a) => Math.max(0, a - 1))}
              disabled={active === 0}
              className="rounded px-3 py-1 text-slate-600 disabled:opacity-40"
            >
              ← Previous
            </button>
            <span className="text-slate-400">
              Day {active + 1} of {logs.length}
            </span>
            <button
              type="button"
              onClick={() => setActive((a) => Math.min(logs.length - 1, a + 1))}
              disabled={active === logs.length - 1}
              className="rounded px-3 py-1 text-slate-600 disabled:opacity-40"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      <div className="hidden print:block">
        {logs.map((log) => (
          <div key={log.date} className="print-page">
            <LogPanel log={log} />
          </div>
        ))}
      </div>
    </Section>
  );
}

function LogPanel({
  log,
  showCalibration,
}: {
  log: DailyLog;
  showCalibration?: boolean;
}) {
  return (
    <div>
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-navy-800">
          {formatDate(log.date)}
        </h3>
        <span className="text-xs text-slate-500">
          {log.from_label} → {log.to_label} · {Math.round(log.total_miles)} mi
        </span>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <DailyLogSheet log={log} showCalibration={showCalibration} />
      </div>

      {/* Accessible status totals (also useful if the image fails to load) */}
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        {(Object.keys(DUTY_STATUS_LABEL) as (keyof typeof DUTY_STATUS_LABEL)[]).map(
          (duty) => (
            <div key={duty} className="rounded bg-slate-50 px-2 py-1">
              <dt className="text-slate-500">{DUTY_STATUS_LABEL[duty]}</dt>
              <dd className="font-semibold text-navy-800">
                {(log.totals[duty] / 60).toFixed(1)} h
              </dd>
            </div>
          ),
        )}
      </dl>
      <p className="mt-2 text-xs text-slate-500">
        <span className="font-medium text-slate-600">Modeled 70-hour recap:</span>{" "}
        on duty today {(log.recap.on_duty_minutes_today / 60).toFixed(1)} h ·
        cycle used {(log.recap.cycle_used_minutes_end_of_day / 60).toFixed(1)} h ·
        available {log.recap.cycle_hours_available.toFixed(1)} h.
      </p>
      <p className="mt-1 text-xs text-slate-400">
        Driver, carrier, vehicle, and shipping values are demo metadata (the
        assessment does not collect these fields).
      </p>
    </div>
  );
}
