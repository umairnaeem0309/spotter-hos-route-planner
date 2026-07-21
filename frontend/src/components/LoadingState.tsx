import { Card } from "./ui/Card";

/** Skeleton shown while a trip plan is generated. */
export function LoadingState() {
  return (
    <div className="space-y-4" aria-busy="true" aria-live="polite">
      <p className="text-sm text-slate-500">
        Generating a compliant trip plan… The backend may take a moment to warm
        up on first request.
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="h-24 animate-pulse bg-slate-100" >
            <span className="sr-only">Loading</span>
          </Card>
        ))}
      </div>
      <Card className="h-72 animate-pulse bg-slate-100" />
      <Card className="h-48 animate-pulse bg-slate-100" />
    </div>
  );
}

export function EmptyState() {
  return (
    <Card className="border-dashed">
      <div className="px-6 py-12 text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-navy-50 text-2xl">
          🗺️
        </div>
        <h3 className="text-base font-semibold text-navy-800">
          Plan a Hours-of-Service compliant trip
        </h3>
        <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
          Enter a current location, pickup, and drop-off, plus your current
          cycle hours. We’ll route the trip, schedule required breaks, fuel
          stops, and rest, and generate daily log sheets.
        </p>
      </div>
    </Card>
  );
}
