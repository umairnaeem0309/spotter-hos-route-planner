import type { TripPlanRequest } from "../../api/trips";

export interface SampleTrip extends TripPlanRequest {
  name: string;
  note: string;
}

/** The four manual-acceptance scenarios from the spec, as one-click samples. */
export const SAMPLE_TRIPS: SampleTrip[] = [
  {
    name: "Short haul (A)",
    note: "Chicago → Indianapolis → Nashville · likely one log day",
    current_location: "Chicago, IL",
    pickup_location: "Indianapolis, IN",
    dropoff_location: "Nashville, TN",
    current_cycle_used_hours: 5,
  },
  {
    name: "Cross-country (B)",
    note: "New York → Pittsburgh → Los Angeles · multiple sleeper + fuel stops",
    current_location: "New York, NY",
    pickup_location: "Pittsburgh, PA",
    dropoff_location: "Los Angeles, CA",
    current_cycle_used_hours: 10,
  },
  {
    name: "Cycle nearly used (C)",
    note: "Chicago → Milwaukee → Dallas · triggers a 34-hour restart",
    current_location: "Chicago, IL",
    pickup_location: "Milwaukee, WI",
    dropoff_location: "Dallas, TX",
    current_cycle_used_hours: 69,
  },
];
