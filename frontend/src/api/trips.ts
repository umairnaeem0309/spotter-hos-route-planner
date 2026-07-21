import type { TripPlan } from "../types/trip";
import { apiGet, apiPost } from "./client";

export interface TripPlanRequest {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
  trip_start?: string;
}

export function planTrip(
  request: TripPlanRequest,
  signal?: AbortSignal,
): Promise<TripPlan> {
  return apiPost<TripPlan>("/trips/plan/", request, signal);
}

export function checkHealth(signal?: AbortSignal): Promise<{ status: string }> {
  return apiGet<{ status: string }>("/health/", signal);
}
