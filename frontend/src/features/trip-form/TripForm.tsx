import { useState } from "react";

import type { TripPlanRequest } from "../../api/trips";
import { Section } from "../../components/ui/Card";
import { SAMPLE_TRIPS } from "./sampleTrips";

interface TripFormProps {
  onSubmit: (request: TripPlanRequest) => void;
  isLoading: boolean;
  /** Field-level errors returned by the API (keyed by field name). */
  fieldErrors?: Record<string, string[]>;
}

interface FormState {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: string;
  trip_start: string;
}

const EMPTY: FormState = {
  current_location: "",
  pickup_location: "",
  dropoff_location: "",
  current_cycle_used_hours: "0",
  trip_start: "",
};

type ClientErrors = Partial<Record<keyof FormState, string>>;

function validate(state: FormState): ClientErrors {
  const errors: ClientErrors = {};
  if (!state.current_location.trim()) errors.current_location = "Required.";
  if (!state.pickup_location.trim()) errors.pickup_location = "Required.";
  if (!state.dropoff_location.trim()) errors.dropoff_location = "Required.";
  const hours = Number(state.current_cycle_used_hours);
  if (
    state.current_cycle_used_hours === "" ||
    Number.isNaN(hours) ||
    hours < 0 ||
    hours > 70
  ) {
    errors.current_cycle_used_hours = "Enter a number between 0 and 70.";
  }
  return errors;
}

export function TripForm({ onSubmit, isLoading, fieldErrors }: TripFormProps) {
  const [state, setState] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<ClientErrors>({});

  const set = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setState((s) => ({ ...s, [key]: e.target.value }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const found = validate(state);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    const request: TripPlanRequest = {
      current_location: state.current_location.trim(),
      pickup_location: state.pickup_location.trim(),
      dropoff_location: state.dropoff_location.trim(),
      current_cycle_used_hours: Number(state.current_cycle_used_hours),
    };
    if (state.trip_start) request.trip_start = new Date(state.trip_start).toISOString();
    onSubmit(request);
  };

  const loadSample = (index: number) => {
    const s = SAMPLE_TRIPS[index];
    setState({
      current_location: s.current_location,
      pickup_location: s.pickup_location,
      dropoff_location: s.dropoff_location,
      current_cycle_used_hours: String(s.current_cycle_used_hours),
      trip_start: "",
    });
    setErrors({});
  };

  const errorFor = (key: keyof FormState): string | undefined =>
    errors[key] ?? fieldErrors?.[key]?.[0];

  return (
    <Section title="Trip details" subtitle="Property-carrying driver, 70-hour / 8-day cycle">
      <form onSubmit={submit} noValidate className="space-y-4">
        <Field
          id="current_location"
          label="Current location"
          value={state.current_location}
          onChange={set("current_location")}
          error={errorFor("current_location")}
          placeholder="Chicago, IL"
        />
        <Field
          id="pickup_location"
          label="Pickup location"
          value={state.pickup_location}
          onChange={set("pickup_location")}
          error={errorFor("pickup_location")}
          placeholder="Indianapolis, IN"
        />
        <Field
          id="dropoff_location"
          label="Drop-off location"
          value={state.dropoff_location}
          onChange={set("dropoff_location")}
          error={errorFor("dropoff_location")}
          placeholder="Dallas, TX"
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field
            id="current_cycle_used_hours"
            label="Current cycle used (hours)"
            type="number"
            value={state.current_cycle_used_hours}
            onChange={set("current_cycle_used_hours")}
            error={errorFor("current_cycle_used_hours")}
            placeholder="0–70"
          />
          <Field
            id="trip_start"
            label="Trip start (optional)"
            type="datetime-local"
            value={state.trip_start}
            onChange={set("trip_start")}
            error={errorFor("trip_start")}
          />
        </div>

        <div className="flex flex-col gap-3 pt-1 sm:flex-row sm:items-center">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-navy-800 focus:outline-none focus:ring-2 focus:ring-navy-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? "Generating…" : "Generate trip plan"}
          </button>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_TRIPS.map((s, i) => (
              <button
                key={s.name}
                type="button"
                onClick={() => loadSample(i)}
                disabled={isLoading}
                title={s.note}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-600 transition hover:border-teal-400 hover:text-teal-700 disabled:opacity-60"
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>
        <p className="text-xs text-slate-400">
          Tip: hover a sample to see the scenario. Set a trip start for
          reproducible results.
        </p>
      </form>
    </Section>
  );
}

interface FieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  type?: string;
  placeholder?: string;
}

function Field({ id, label, value, onChange, error, type = "text", placeholder }: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        min={type === "number" ? 0 : undefined}
        max={type === "number" ? 70 : undefined}
        step={type === "number" ? "0.5" : undefined}
        className={`mt-1 w-full rounded-lg border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 ${
          error
            ? "border-rose-400 focus:ring-rose-300"
            : "border-slate-300 focus:border-teal-400 focus:ring-teal-200"
        }`}
      />
      {error && (
        <p id={`${id}-error`} className="mt-1 text-xs text-rose-600">
          {error}
        </p>
      )}
    </div>
  );
}
