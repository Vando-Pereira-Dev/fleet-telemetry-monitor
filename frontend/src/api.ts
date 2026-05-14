import type {
  FleetStatusCountsOut,
  FleetVehiclesSnapshotOut,
  ZonesCountsOut,
} from "./types";

const baseUrl =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

async function fetchJson<T>(path: string): Promise<T> {
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  return (await response.json()) as T;
}

export function getVehiclesSnapshot(): Promise<FleetVehiclesSnapshotOut> {
  return fetchJson<FleetVehiclesSnapshotOut>("/vehicles");
}

export function getZoneCounts(): Promise<ZonesCountsOut> {
  return fetchJson<ZonesCountsOut>("/zones/counts");
}

export function getFleetState(): Promise<FleetStatusCountsOut> {
  return fetchJson<FleetStatusCountsOut>("/fleet/state");
}
