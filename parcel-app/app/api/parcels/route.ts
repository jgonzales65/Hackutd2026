import { NextResponse } from "next/server";
import type { Parcel } from "@/lib/types";

const sq = (lng: number, lat: number, s = 0.0015): [number, number][][] => [
  [[lng, lat], [lng + s, lat], [lng + s, lat + s], [lng, lat + s], [lng, lat]],
];

const parcels: Parcel[] = [
  {
    id: "P-101", address: "1420 McKinney Ave", zip: "75204", owner: "Harlan Row Holdings LLC",
    score: 72, breakdown: { flood: 85, title: 80, permits: 40, zoning: 30 },
    findings: [
      { category: "Flood", text: "In FEMA 100-year floodplain", confidence: "High",
        source: "FEMA flood map", impact: "Lenders require flood insurance, which adds yearly cost and can delay closing." },
      { category: "Title", text: "Open contractor lien found", confidence: "Medium",
        source: "County clerk PDF (AI-parsed)", impact: "An unpaid lien can block closing or pass the debt to the buyer." },
    ],
    coordinates: sq(-96.801, 32.78),
  },
  {
    id: "P-102", address: "1500 McKinney Ave", zip: "75204", owner: "Cedar Ridge Partners",
    score: 35, breakdown: { flood: 20, title: 25, permits: 65, zoning: 15 },
    findings: [
      { category: "Permits", text: "Permit expired without sign-off", confidence: "Medium",
        source: "City permit portal", impact: "Unpermitted work may need rework before the building can be occupied." },
    ],
    coordinates: sq(-96.799, 32.78),
  },
  {
    id: "P-103", address: "1420 Main St", zip: "75202", owner: "Alder Land Trust",
    score: 18, breakdown: { flood: 10, title: 15, permits: 20, zoning: 10 },
    findings: [],
    coordinates: sq(-96.801, 32.778),
  },
  {
    id: "P-104", address: "1500 Main St", zip: "75202", owner: "Harlan Row Holdings LLC",
    score: 55, breakdown: { flood: 25, title: 70, permits: 30, zoning: 65 },
    findings: [
      { category: "Zoning", text: "Zoning may not allow the planned use", confidence: "Low",
        source: "Zoning notice PDF (AI-parsed)", impact: "If the use is not allowed, the project can stall until a variance is granted." },
      { category: "Title", text: "Owner also holds P-101, which has an open lien", confidence: "Medium",
        source: "Ownership graph", impact: "Linked liens can complicate negotiations and closing." },
    ],
    coordinates: sq(-96.799, 32.778),
  },
];

export async function GET() {
  return NextResponse.json(parcels);
}