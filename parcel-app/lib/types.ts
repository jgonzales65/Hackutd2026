import type { assessFlood } from './flood-scoring';
export type Finding = {
  category: string;
  text: string;
  confidence: "High" | "Medium" | "Low";
  source: string;
  impact: string;
  snippet?: string;
  cure?: { label: string; days: number; cost: number; reduces: number };
};

export type RecordAddress = { source: string; value: string };

export type Parcel = {
  id: string;
  address: string;
  zip: string;
  owner: string;
  score: number | null;
  assessment?: ReturnType<typeof assessFlood>;
  breakdown: { environmental: number | null; financial: number | null; flood: number | null; title: number | null; permits: number | null; zoning: number | null };
  findings: Finding[];
  coordinates: [number, number][][];
  geometry?: GeoJSON.Polygon | GeoJSON.MultiPolygon;
  flood?: { available: boolean; coverageComplete: boolean; matches: {
    zone: string; subtype: string | null; sfha: boolean | null;
    source: string; citation: string | null; retrievedAt: string;
  }[] };
  records?: RecordAddress[];
  listingPin?: [number, number];
};