import type { Parcel } from "./types";

export function centroid(p: Parcel): [number, number] {
  const ring = p.coordinates[0];
  return [
    ring.reduce((a, c) => a + c[0], 0) / ring.length,
    ring.reduce((a, c) => a + c[1], 0) / ring.length,
  ];
}

export function meters(a: [number, number], b: [number, number]) {
  const R = 6371000, rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b[1] - a[1]), dLng = rad(b[0] - a[0]);
  const h = Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a[1])) * Math.cos(rad(b[1])) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}