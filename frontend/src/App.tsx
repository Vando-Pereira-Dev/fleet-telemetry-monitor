import { useCallback, useEffect, useMemo, useState } from "react";
import { getFleetState, getVehiclesSnapshot, getZoneCounts } from "./api";
import type {
  FleetStatusCountsOut,
  FleetVehicleRow,
  FleetVehiclesSnapshotOut,
  ZonesCountsOut,
} from "./types";

const POLL_MS = 2500;

function formatTs(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function statusTone(status: string): string {
  switch (status) {
    case "fault":
      return "var(--fault)";
    case "charging":
      return "var(--charging)";
    case "moving":
      return "var(--moving)";
    case "idle":
    default:
      return "var(--idle)";
  }
}

export default function App() {
  const [snapshot, setSnapshot] = useState<FleetVehiclesSnapshotOut | null>(null);
  const [zones, setZones] = useState<ZonesCountsOut | null>(null);
  const [fleet, setFleet] = useState<FleetStatusCountsOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastOkAt, setLastOkAt] = useState<Date | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [v, z, f] = await Promise.all([
        getVehiclesSnapshot(),
        getZoneCounts(),
        getFleetState(),
      ]);
      setSnapshot(v);
      setZones(z);
      setFleet(f);
      setError(null);
      setLastOkAt(new Date());
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e);
      setError(message);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), POLL_MS);
    return () => window.clearInterval(id);
  }, [refresh]);

  const vehicles = useMemo(() => snapshot?.vehicles ?? [], [snapshot]);

  return (
    <div style={{ padding: "20px 22px 40px", maxWidth: 1280, margin: "0 auto" }}>
      <header
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: 16,
          marginBottom: 18,
          borderBottom: `1px solid ${"var(--border)"}`,
          paddingBottom: 16,
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", letterSpacing: 0.6 }}>
            Fleet Telemetry Monitor
          </div>
          <h1 style={{ margin: "6px 0 0", fontSize: 26, fontWeight: 650, letterSpacing: -0.4 }}>
            Live fleet overview
          </h1>
          <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
            Polling every {POLL_MS / 1000}s · API{" "}
            <span style={{ color: "var(--text)" }}>
              {import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"}
            </span>
            {lastOkAt ? (
              <>
                {" "}
                · Last refresh:{" "}
                <span style={{ color: "var(--text)" }}>{lastOkAt.toLocaleTimeString()}</span>
              </>
            ) : null}
          </div>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "flex-end" }}>
          {fleet ? (
            <>
              <Chip label="Total" value={fleet.total} />
              <Chip label="Idle" value={fleet.idle} />
              <Chip label="Moving" value={fleet.moving} tone="moving" />
              <Chip label="Charging" value={fleet.charging} tone="charging" />
              <Chip label="Fault" value={fleet.fault} tone="fault" />
            </>
          ) : (
            <Chip label="Fleet" value="…" />
          )}
        </div>
      </header>

      {error ? (
        <div
          style={{
            border: "1px solid rgba(255,107,107,0.35)",
            background: "rgba(255,107,107,0.08)",
            color: "var(--danger)",
            padding: "12px 14px",
            borderRadius: 10,
            marginBottom: 16,
            fontSize: 13,
          }}
        >
          <strong>Could not reach the API.</strong> {error}
        </div>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 320px",
          gap: 16,
          alignItems: "start",
        }}
        className="layout"
      >
        <section
          style={{
            border: `1px solid var(--border)`,
            background: "linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%)",
            borderRadius: 12,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "12px 14px",
              borderBottom: `1px solid var(--border)`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "baseline",
              gap: 12,
            }}
          >
            <div style={{ fontWeight: 650 }}>Vehicles ({vehicles.length})</div>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>Status · Battery · Latest anomaly</div>
          </div>

          <div style={{ overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 860 }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: 12, color: "var(--muted)" }}>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Vehicle</th>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Status</th>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Battery</th>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Last event</th>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Latest anomaly</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map((v) => (
                  <VehicleRow key={v.vehicle_id} v={v} />
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside
          style={{
            border: `1px solid var(--border)`,
            background: "linear-gradient(180deg, var(--panel) 0%, var(--panel-2) 100%)",
            borderRadius: 12,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "12px 14px",
              borderBottom: `1px solid var(--border)`,
              fontWeight: 650,
            }}
          >
            Zone entry counts
          </div>
          <div style={{ maxHeight: "78vh", overflow: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: 12, color: "var(--muted)" }}>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Zone</th>
                  <th style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)` }}>Entries</th>
                </tr>
              </thead>
              <tbody>
                {(zones?.zones ?? []).map((z) => (
                  <tr key={z.zone_id}>
                    <td style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)`, fontSize: 13 }}>
                      <code style={{ color: "var(--text)" }}>{z.zone_id}</code>
                    </td>
                    <td
                      style={{
                        padding: "10px 12px",
                        borderBottom: `1px solid var(--border)`,
                        fontVariantNumeric: "tabular-nums",
                        fontWeight: 650,
                      }}
                    >
                      {z.entry_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </aside>
      </div>

      <footer style={{ marginTop: 16, fontSize: 12, color: "var(--muted)" }}>
        Dashboard uses short-interval polling (simple operations footprint, works through corporate proxies). For
        sub-second push, upgrade path is WebSockets or SSE plus a cache layer.
      </footer>
    </div>
  );
}

function Chip(props: { label: string; value: number | string; tone?: "moving" | "charging" | "fault" }) {
  const border =
    props.tone === "fault"
      ? "rgba(251,113,133,0.35)"
      : props.tone === "charging"
        ? "rgba(96,165,250,0.35)"
        : props.tone === "moving"
          ? "rgba(52,211,153,0.35)"
          : "var(--border)";
  return (
    <div
      style={{
        border: `1px solid ${border}`,
        background: "rgba(255,255,255,0.03)",
        borderRadius: 999,
        padding: "7px 10px",
        display: "flex",
        gap: 8,
        alignItems: "baseline",
        fontSize: 12,
        color: "var(--muted)",
      }}
    >
      <span>{props.label}</span>
      <span style={{ color: "var(--text)", fontWeight: 750, fontVariantNumeric: "tabular-nums" }}>
        {props.value}
      </span>
    </div>
  );
}

function VehicleRow(props: { v: FleetVehicleRow }) {
  const { v } = props;
  const pct = v.battery_pct ?? 0;
  const barColor =
    pct <= 10 ? "var(--danger)" : pct <= 25 ? "var(--warn)" : pct <= 50 ? "var(--accent)" : "var(--ok)";

  return (
    <tr>
      <td style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)`, verticalAlign: "top" }}>
        <div style={{ fontWeight: 750, letterSpacing: -0.2 }}>{v.vehicle_id}</div>
      </td>
      <td style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)`, verticalAlign: "top" }}>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            border: `1px solid var(--border)`,
            borderRadius: 999,
            padding: "6px 10px",
            fontSize: 12,
            color: "var(--text)",
            background: "rgba(255,255,255,0.03)",
          }}
        >
          <span
            aria-hidden
            style={{
              width: 8,
              height: 8,
              borderRadius: 999,
              background: statusTone(v.current_status),
            }}
          />
          <span style={{ textTransform: "capitalize" }}>{v.current_status}</span>
        </span>
      </td>
      <td style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)`, verticalAlign: "top", width: 220 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
          <div style={{ fontVariantNumeric: "tabular-nums", fontWeight: 750 }}>{v.battery_pct ?? "—"}%</div>
        </div>
        <div
          style={{
            marginTop: 8,
            height: 8,
            borderRadius: 999,
            background: "rgba(255,255,255,0.06)",
            overflow: "hidden",
            border: `1px solid var(--border)`,
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${Math.max(0, Math.min(100, pct))}%`,
              background: barColor,
            }}
          />
        </div>
      </td>
      <td
        style={{
          padding: "10px 12px",
          borderBottom: `1px solid var(--border)`,
          verticalAlign: "top",
          fontSize: 12,
          color: "var(--muted)",
          whiteSpace: "nowrap",
        }}
      >
        {formatTs(v.last_event_ts)}
      </td>
      <td style={{ padding: "10px 12px", borderBottom: `1px solid var(--border)`, verticalAlign: "top" }}>
        {v.latest_anomaly ? (
          <div style={{ display: "grid", gap: 6 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "baseline" }}>
              <code style={{ fontSize: 12, color: "var(--text)" }}>{v.latest_anomaly.anomaly_type}</code>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>
                {formatTs(v.latest_anomaly.detected_at)}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.35 }}>
              {summarizeDetail(v.latest_anomaly.detail)}
            </div>
          </div>
        ) : (
          <span style={{ color: "var(--muted)", fontSize: 12 }}>None</span>
        )}
      </td>
    </tr>
  );
}

function summarizeDetail(detail: Record<string, unknown>): string {
  const keys = Object.keys(detail);
  if (keys.length === 0) return "—";
  try {
    return JSON.stringify(detail);
  } catch {
    return "—";
  }
}
