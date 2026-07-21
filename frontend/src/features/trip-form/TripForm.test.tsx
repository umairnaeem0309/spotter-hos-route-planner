import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TripForm } from "./TripForm";

describe("TripForm", () => {
  it("blocks submit and shows inline errors when required fields are blank", async () => {
    const onSubmit = vi.fn();
    render(<TripForm onSubmit={onSubmit} isLoading={false} />);

    await userEvent.click(screen.getByRole("button", { name: /generate trip plan/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getAllByText("Required.").length).toBeGreaterThanOrEqual(3);
  });

  it("rejects cycle hours outside 0–70", async () => {
    const onSubmit = vi.fn();
    render(<TripForm onSubmit={onSubmit} isLoading={false} />);

    await userEvent.type(screen.getByLabelText(/current location/i), "Chicago, IL");
    await userEvent.type(screen.getByLabelText(/pickup location/i), "Indianapolis, IN");
    await userEvent.type(screen.getByLabelText(/drop-off location/i), "Nashville, TN");
    const cycle = screen.getByLabelText(/current cycle used/i);
    await userEvent.clear(cycle);
    await userEvent.type(cycle, "99");
    await userEvent.click(screen.getByRole("button", { name: /generate trip plan/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/between 0 and 70/i)).toBeInTheDocument();
  });

  it("loads a sample trip and submits the request", async () => {
    const onSubmit = vi.fn();
    render(<TripForm onSubmit={onSubmit} isLoading={false} />);

    await userEvent.click(screen.getByRole("button", { name: /short haul/i }));
    expect(screen.getByLabelText(/current location/i)).toHaveValue("Chicago, IL");

    await userEvent.click(screen.getByRole("button", { name: /generate trip plan/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      current_location: "Chicago, IL",
      pickup_location: "Indianapolis, IN",
      dropoff_location: "Nashville, TN",
      current_cycle_used_hours: 5,
    });
  });

  it("surfaces server field errors", () => {
    render(
      <TripForm
        onSubmit={vi.fn()}
        isLoading={false}
        fieldErrors={{ dropoff_location: ["No matching location was found."] }}
      />,
    );
    expect(screen.getByText(/no matching location/i)).toBeInTheDocument();
  });
});
