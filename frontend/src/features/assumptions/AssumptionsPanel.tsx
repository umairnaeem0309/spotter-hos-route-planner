import { useState } from "react";

import { Card } from "../../components/ui/Card";

interface AssumptionsPanelProps {
  assumptions: string[];
  warnings: string[];
}

export function AssumptionsPanel({ assumptions, warnings }: AssumptionsPanelProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-3">
      {warnings.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <div className="px-5 py-4">
            <h3 className="text-sm font-semibold text-amber-800">
              Please note
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        </Card>
      )}

      <Card>
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="flex w-full items-center justify-between px-5 py-4 text-left"
        >
          <span className="text-sm font-semibold text-navy-800">
            Calculation assumptions
          </span>
          <span className="text-slate-400" aria-hidden>
            {open ? "▲" : "▼"}
          </span>
        </button>
        {open && (
          <ul className="list-disc space-y-1.5 border-t border-slate-100 px-5 py-4 pl-9 text-sm text-slate-600">
            {assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
