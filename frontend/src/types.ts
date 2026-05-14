export type LatestAnomalyBrief = {
  id: number;
  detected_at: string;
  anomaly_type: string;
  detail: Record<string, unknown>;
};

export type FleetVehicleRow = {
  vehicle_id: string;
  current_status: string;
  battery_pct: number | null;
  last_event_ts: string | null;
  latest_anomaly: LatestAnomalyBrief | null;
};

export type FleetVehiclesSnapshotOut = {
  vehicles: FleetVehicleRow[];
};

export type ZoneCountOut = {
  zone_id: string;
  entry_count: number;
};

export type ZonesCountsOut = {
  zones: ZoneCountOut[];
};

export type FleetStatusCountsOut = {
  idle: number;
  moving: number;
  charging: number;
  fault: number;
  total: number;
};
