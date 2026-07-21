import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../api/client";
import * as tripsApi from "../api/trips";
import { SAMPLE_PLAN } from "../test/fixtures";
import { TripPlannerPage } from "./TripPlannerPage";

// MapLibre needs WebGL; stub it so the page can render under jsdom.
vi.mock("maplibre-gl", () => {
  class Stub {
    on() {}
    addControl() {}
    remove() {}
    addSource() {}
    addLayer() {}
    fitBounds() {}
    setLngLat() {
      return this;
    }
    setPopup() {
      return this;
    }
    addTo() {
      return this;
    }
    setText() {
      return this;
    }
    extend() {
      return this;
    }
  }
  return {
    default: {
      Map: Stub,
      Marker: Stub,
      Popup: Stub,
      NavigationControl: Stub,
      LngLatBounds: Stub,
    },
  };
});

async function fillAndSubmit() {
  await userEvent.click(screen.getByRole("button", { name: /short haul/i }));
  await userEvent.click(screen.getByRole("button", { name: /generate trip plan/i }));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("TripPlannerPage", () => {
  it("shows the empty state initially", () => {
    render(<TripPlannerPage />);
    expect(screen.getByText(/plan a hours-of-service compliant trip/i)).toBeInTheDocument();
  });

  it("renders summary, timeline, and instructions on success", async () => {
    vi.spyOn(tripsApi, "planTrip").mockResolvedValue(SAMPLE_PLAN);
    render(<TripPlannerPage />);

    await fillAndSubmit();

    await waitFor(() =>
      expect(screen.getByText(/hos-compliant schedule/i)).toBeInTheDocument(),
    );
    // Summary metric.
    expect(screen.getByText(/total distance/i)).toBeInTheDocument();
    // Timeline shows pickup and drop-off (also present in the map legend).
    expect(screen.getAllByText("Pickup").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Drop-off").length).toBeGreaterThanOrEqual(1);
    // Route instructions accordion.
    expect(screen.getByText(/turn-by-turn directions/i)).toBeInTheDocument();
  });

  it("renders a helpful error state on API failure", async () => {
    vi.spyOn(tripsApi, "planTrip").mockRejectedValue(
      new ApiError("no_route_found", "No drivable route was found.", 400),
    );
    render(<TripPlannerPage />);

    await fillAndSubmit();

    await waitFor(() =>
      expect(screen.getByText(/no route found/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/no drivable route was found/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("maps server validation errors onto form fields", async () => {
    vi.spyOn(tripsApi, "planTrip").mockRejectedValue(
      new ApiError("validation_error", "Invalid.", 400, {
        pickup_location: ["No matching location was found."],
      }),
    );
    render(<TripPlannerPage />);

    await fillAndSubmit();

    await waitFor(() =>
      expect(screen.getByText(/no matching location/i)).toBeInTheDocument(),
    );
  });
});
