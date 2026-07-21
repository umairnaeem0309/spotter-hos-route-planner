import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

import type { TimelineEvent, TripRoute } from "../../types/trip";
import { EVENT_DISPLAY } from "../../lib/format";

interface RouteMapProps {
  route: TripRoute;
  timeline: TimelineEvent[];
}

const OPENFREEMAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

// Event types that get their own marker on the map.
const STOP_TYPES: TimelineEvent["type"][] = [
  "fuel",
  "rest_break",
  "sleeper_berth",
  "cycle_restart",
];

const WAYPOINT_COLORS: Record<string, string> = {
  current: "#1f3a5f",
  pickup: "#059669",
  dropoff: "#2563eb",
};

function markerEl(color: string, glyph: string): HTMLDivElement {
  const el = document.createElement("div");
  el.style.cssText = `
    width: 26px; height: 26px; border-radius: 50%;
    background: ${color}; color: #fff; display: flex;
    align-items: center; justify-content: center; font-size: 13px;
    border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.4);
  `;
  el.textContent = glyph;
  return el;
}

export function RouteMap({ route, timeline }: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OPENFREEMAP_STYLE,
      center: route.waypoints[0]?.coordinate ?? [-98, 39],
      zoom: 4,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    map.on("load", () => {
      const coords = route.geometry.coordinates;
      if (coords.length > 1) {
        map.addSource("route", {
          type: "geojson",
          data: {
            type: "Feature",
            properties: {},
            geometry: { type: "LineString", coordinates: coords },
          },
        });
        map.addLayer({
          id: "route-line",
          type: "line",
          source: "route",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: { "line-color": "#0d9488", "line-width": 4 },
        });

        const bounds = coords.reduce(
          (b, c) => b.extend(c as [number, number]),
          new maplibregl.LngLatBounds(
            coords[0] as [number, number],
            coords[0] as [number, number],
          ),
        );
        map.fitBounds(bounds, { padding: 48, duration: 0 });
      }

      // Waypoint markers.
      route.waypoints.forEach((wp) => {
        const glyph = wp.type === "current" ? "◉" : wp.type === "pickup" ? "P" : "D";
        new maplibregl.Marker({ element: markerEl(WAYPOINT_COLORS[wp.type], glyph) })
          .setLngLat(wp.coordinate)
          .setPopup(new maplibregl.Popup({ offset: 18 }).setText(`${wp.type}: ${wp.label}`))
          .addTo(map);
      });

      // Stop markers (fuel, rest, sleeper, restart).
      timeline
        .filter((e) => STOP_TYPES.includes(e.type) && e.coordinate)
        .forEach((e) => {
          const display = EVENT_DISPLAY[e.type];
          new maplibregl.Marker({ element: markerEl(display.color, display.icon) })
            .setLngLat(e.coordinate as [number, number])
            .setPopup(
              new maplibregl.Popup({ offset: 18 }).setText(
                `${display.label} · ${e.location_label}`,
              ),
            )
            .addTo(map);
        });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [route, timeline]);

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className="h-[440px] w-full overflow-hidden rounded-xl border border-slate-200"
        role="region"
        aria-label="Route map"
      />
      <MapLegend />
    </div>
  );
}

function MapLegend() {
  const items = [
    { color: WAYPOINT_COLORS.current, label: "Current" },
    { color: WAYPOINT_COLORS.pickup, label: "Pickup" },
    { color: WAYPOINT_COLORS.dropoff, label: "Drop-off" },
    { color: EVENT_DISPLAY.fuel.color, label: "Fuel" },
    { color: EVENT_DISPLAY.rest_break.color, label: "Break" },
    { color: EVENT_DISPLAY.sleeper_berth.color, label: "Sleeper" },
    { color: EVENT_DISPLAY.cycle_restart.color, label: "Restart" },
  ];
  return (
    <div className="absolute bottom-3 left-3 rounded-lg border border-slate-200 bg-white/95 p-2 text-xs shadow-sm backdrop-blur">
      <ul className="grid grid-cols-2 gap-x-3 gap-y-1">
        {items.map((it) => (
          <li key={it.label} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full border border-white shadow"
              style={{ backgroundColor: it.color }}
            />
            <span className="text-slate-600">{it.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
