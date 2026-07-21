/**
 * Thin fetch wrapper around the Django API.
 *
 * - Reads the base URL from VITE_API_BASE_URL (public config, not a secret).
 * - Surfaces the canonical error schema as a typed `ApiError`.
 * - Accepts an AbortSignal so callers can cancel stale requests.
 */
import type { ApiErrorBody } from "../types/trip";

const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"
).replace(/\/$/, "");

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly fieldErrors?: Record<string, string[]>;

  constructor(
    code: string,
    message: string,
    status: number,
    fieldErrors?: Record<string, string[]>,
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorBody).error?.code === "string"
  );
}

async function parseError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // Non-JSON error (e.g. a proxy 502 HTML page).
  }
  if (isApiErrorBody(body)) {
    const { code, message, details } = body.error;
    const fieldErrors =
      details && typeof details === "object"
        ? (details as Record<string, string[]>)
        : undefined;
    return new ApiError(code, message, response.status, fieldErrors);
  }
  return new ApiError(
    "network_error",
    `Request failed with status ${response.status}.`,
    response.status,
  );
}

export async function apiPost<T>(
  path: string,
  payload: unknown,
  signal?: AbortSignal,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw err; // let callers ignore cancelled requests
    }
    throw new ApiError(
      "network_error",
      "Could not reach the server. Please check your connection and try again.",
      0,
    );
  }

  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as T;
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { signal });
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as T;
}

export { BASE_URL };
