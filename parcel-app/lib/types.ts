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
  score: number;
  breakdown: { flood: number; title: number; permits: number; zoning: number };
  findings: Finding[];
  coordinates: [number, number][][];
  records?: RecordAddress[];
  listingPin?: [number, number];
};