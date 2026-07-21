import { useRef, useState } from "react";

import { ApiError } from "../api/client";
import { planTrip, type TripPlanRequest } from "../api/trips";
import { ErrorState } from "../components/ErrorState";
import { EmptyState, LoadingState } from "../components/LoadingState";
import { AssumptionsPanel } from "../features/assumptions/AssumptionsPanel";
import { DailyLogs } from "../features/logs/DailyLogs";
import { RouteMap } from "../features/map/RouteMap";
import { RouteInstructions } from "../features/route-instructions/RouteInstructions";
import { SummaryCards } from "../features/summary/SummaryCards";
import { Timeline } from "../features/timeline/Timeline";
import { TripForm } from "../features/trip-form/TripForm";
import type { TripPlan } from "../types/trip";

type Status = "idle" | "loading" | "success" | "error";

export function TripPlannerPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastRequest, setLastRequest] = useState<TripPlanRequest | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const submit = async (request: TripPlanRequest) => {
    // Cancel any in-flight request so a slow earlier response can't overwrite
    // a newer one (stale-request protection).
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus("loading");
    setError(null);
    setLastRequest(request);

    try {
      const result = await planTrip(request, controller.signal);
      if (controller.signal.aborted) return;
      setPlan(result);
      setStatus("success");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(
        err instanceof ApiError
          ? err
          : new ApiError("unknown", "An unexpected error occurred.", 0),
      );
      setStatus("error");
    }
  };

  const fieldErrors =
    error?.code === "validation_error" ? error.fieldErrors : undefined;

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 lg:py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-navy-800 lg:text-3xl">
          HOS Route Planner
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Property-Carrying Driver Trip &amp; ELD Log Planner
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(320px,380px)_1fr]">
        <div className="lg:sticky lg:top-6 lg:self-start">
          <TripForm onSubmit={submit} isLoading={status === "loading"} fieldErrors={fieldErrors} />
        </div>

        <div className="min-w-0 space-y-6">
          {status === "idle" && <EmptyState />}
          {status === "loading" && <LoadingState />}
          {status === "error" && error && (
            <ErrorState
              title={errorTitle(error)}
              message={error.message}
              onRetry={lastRequest ? () => submit(lastRequest) : undefined}
            />
          )}
          {status === "success" && plan && <Results plan={plan} />}
        </div>
      </div>

      <footer className="mt-10 border-t border-slate-200 pt-4 text-center text-xs text-slate-400">
        Assessment/demo planner — not a certified ELD or legal-compliance
        product. Map data © OpenStreetMap contributors, tiles by OpenFreeMap.
      </footer>
    </div>
  );
}

function errorTitle(error: ApiError): string {
  if (error.code === "validation_error") return "Please fix the highlighted fields";
  if (error.code === "address_not_found") return "Location not found";
  if (error.code === "no_route_found") return "No route found";
  if (error.status >= 500 || error.status === 0) return "Service unavailable";
  return "Something went wrong";
}

function Results({ plan }: { plan: TripPlan }) {
  return (
    <>
      <SummaryCards summary={plan.summary} />
      <RouteMap route={plan.route} timeline={plan.timeline} />
      <Timeline events={plan.timeline} />
      <DailyLogs logs={plan.daily_logs} />
      <RouteInstructions instructions={plan.route.instructions} />
      <AssumptionsPanel assumptions={plan.assumptions} warnings={plan.warnings} />
    </>
  );
}
