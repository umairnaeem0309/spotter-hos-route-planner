import { Suspense, lazy, useRef, useState } from "react";

import { ApiError } from "../api/client";
import { planTrip, type TripPlanRequest } from "../api/trips";
import { BrandMark } from "../components/ui/Icon";
import { ErrorState } from "../components/ErrorState";
import { EmptyState, LoadingState } from "../components/LoadingState";
import { AssumptionsPanel } from "../features/assumptions/AssumptionsPanel";
import { DailyLogs } from "../features/logs/DailyLogs";
import { RouteInstructions } from "../features/route-instructions/RouteInstructions";
import { SummaryCards } from "../features/summary/SummaryCards";
import { Timeline } from "../features/timeline/Timeline";
import { TripForm } from "../features/trip-form/TripForm";
import type { TripPlan } from "../types/trip";

// MapLibre is large; load it only when results exist so it stays out of the
// initial bundle.
const RouteMap = lazy(() =>
  import("../features/map/RouteMap").then((m) => ({ default: m.RouteMap })),
);

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
      <header className="mb-6 flex items-center gap-3 border-b border-slate-200 pb-5">
        <BrandMark size={40} />
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-navy-800 lg:text-3xl">
            HOS Route Planner
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Property-Carrying Driver Trip &amp; ELD Log Planner
          </p>
        </div>
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
    <div className="animate-fade-in-up space-y-6">
      <SummaryCards summary={plan.summary} />
      <Suspense
        fallback={
          <div className="h-[440px] w-full animate-pulse rounded-xl border border-slate-200 bg-slate-100" />
        }
      >
        <RouteMap route={plan.route} timeline={plan.timeline} />
      </Suspense>
      <Timeline events={plan.timeline} />
      <DailyLogs logs={plan.daily_logs} />
      <RouteInstructions instructions={plan.route.instructions} />
      <AssumptionsPanel assumptions={plan.assumptions} warnings={plan.warnings} />
    </div>
  );
}
