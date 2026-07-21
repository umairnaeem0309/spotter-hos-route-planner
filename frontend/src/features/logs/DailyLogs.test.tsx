import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { DailyLog } from "../../types/trip";
import { SAMPLE_PLAN } from "../../test/fixtures";
import { DailyLogs } from "./DailyLogs";

const base = SAMPLE_PLAN.daily_logs[0];
const twoLogs: DailyLog[] = [
  { ...base, date: "2026-07-20" },
  { ...base, date: "2026-07-21", from_label: "Indianapolis, IN", to_label: "Dallas, TX" },
];

describe("DailyLogs", () => {
  it("renders a single log without navigation", () => {
    render(<DailyLogs logs={[base]} />);
    expect(screen.getByText(/driver daily logs/i)).toBeInTheDocument();
    expect(screen.queryByText(/day 1 of/i)).not.toBeInTheDocument();
  });

  it("navigates between multiple logs with Next/Previous", async () => {
    render(<DailyLogs logs={twoLogs} />);
    expect(screen.getByText(/day 1 of 2/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText(/day 2 of 2/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /previous/i }));
    expect(screen.getByText(/day 1 of 2/i)).toBeInTheDocument();
  });

  it("jumps to a day via its tab", async () => {
    render(<DailyLogs logs={twoLogs} />);
    const tabs = screen.getAllByRole("button", { name: /day 2/i });
    await userEvent.click(tabs[0]);
    expect(screen.getByText(/day 2 of 2/i)).toBeInTheDocument();
  });

  it("renders the duty-status graph as an SVG polyline", () => {
    const { container } = render(<DailyLogs logs={[base]} />);
    const polyline = container.querySelector("polyline");
    expect(polyline).not.toBeNull();
    // Points reference the grid coordinates.
    expect(polyline?.getAttribute("points")?.length).toBeGreaterThan(0);
  });
});
