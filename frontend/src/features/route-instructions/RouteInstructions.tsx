import { useState } from "react";

import type { RouteInstruction } from "../../types/trip";
import { Section } from "../../components/ui/Card";
import { formatDuration } from "../../lib/format";

interface RouteInstructionsProps {
  instructions: RouteInstruction[];
}

export function RouteInstructions({ instructions }: RouteInstructionsProps) {
  const [open, setOpen] = useState(false);

  if (instructions.length === 0) return null;

  const visible = open ? instructions : instructions.slice(0, 6);

  return (
    <Section
      title="Turn-by-turn directions"
      subtitle={`${instructions.length} steps`}
    >
      <ol className="divide-y divide-slate-100">
        {visible.map((step, index) => (
          <li key={index} className="flex items-start gap-3 py-2">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy-50 text-xs font-semibold text-navy-700">
              {index + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm text-slate-700">
                {step.text || step.name || "Continue"}
              </p>
              <p className="text-xs text-slate-400">
                {step.distance_miles.toLocaleString(undefined, {
                  maximumFractionDigits: 1,
                })}{" "}
                mi · {formatDuration(step.duration_minutes)}
              </p>
            </div>
          </li>
        ))}
      </ol>
      {instructions.length > 6 && (
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="mt-3 text-sm font-medium text-teal-700 hover:text-teal-800"
        >
          {open ? "Show fewer" : `Show all ${instructions.length} steps`}
        </button>
      )}
    </Section>
  );
}
