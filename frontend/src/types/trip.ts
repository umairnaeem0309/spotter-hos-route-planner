/**
 * Strict TypeScript types mirroring the Django `POST /api/trips/plan/`
 * response contract and the canonical error schema. Keep these in sync with
 * `backend/apps/trips/services/trip_planner.py`.
 */

export type Coordinate = [number, number]; // [lon, lat]

export type DutyStatus =
  | "OFF_DUTY"
  | "SLEEPER_BERTH"
  | "DRIVING"
  | "ON_DUTY_NOT_DRIVING";

export type EventType =
  | "driving"
  | "pickup"
  | "dropoff"
  | "fuel"
  | "rest_break"
  | "sleeper_berth"
  | "cycle_restart";

export interface TripInput {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
  trip_start: string;
}

export interface TripSummary {
  total_distance_miles: number;
  raw_driving_minutes: number;
  compliant_trip_minutes: number;
  departure_at: string;
  arrival_at: string;
  number_of_log_days: number;
  fuel_stop_count: number;
  rest_break_count: number;
  overnight_rest_count: number;
  cycle_restart_count: number;
}

export interface RouteWaypoint {
  type: "current" | "pickup" | "dropoff";
  label: string;
  coordinate: Coordinate;
}

export interface RouteInstruction {
  text: string;
  name: string;
  distance_miles: number;
  duration_minutes: number;
}

export interface TripRoute {
  geometry: {
    type: "LineString";
    coordinates: Coordinate[];
  };
  waypoints: RouteWaypoint[];
  instructions: RouteInstruction[];
}

export interface TimelineEvent {
  type: EventType;
  duty_status: DutyStatus;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  distance_miles: number;
  coordinate: Coordinate | null;
  location_label: string;
  description: string;
  reason_code: string;
}

export interface DailyLogSegment {
  duty_status: DutyStatus;
  start_minute: number;
  end_minute: number;
  event_type: EventType | null;
  is_event_start: boolean;
  label: string;
}

export interface DailyLogRemark {
  time: string;
  location: string;
  activity: string;
}

export interface DailyLogRecap {
  on_duty_minutes_today: number;
  cycle_used_minutes_end_of_day: number;
  cycle_hours_available: number;
}

export interface DailyLogMetadata {
  driver_name: string;
  carrier: string;
  main_office: string;
  vehicle: string;
  shipping_document: string;
  is_demo: boolean;
}

export interface DailyLog {
  date: string;
  from_label: string;
  to_label: string;
  total_miles: number;
  segments: DailyLogSegment[];
  totals: Record<DutyStatus, number>;
  remarks: DailyLogRemark[];
  recap: DailyLogRecap;
  metadata: DailyLogMetadata;
}

export interface TripPlan {
  trip_id: string;
  input: TripInput;
  summary: TripSummary;
  route: TripRoute;
  timeline: TimelineEvent[];
  daily_logs: DailyLog[];
  assumptions: string[];
  warnings: string[];
}

/** Canonical API error body: { error: { code, message, details? } }. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]> | Record<string, unknown>;
  };
}
