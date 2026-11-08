import type { Parcel } from "./types";

const ABBR: Record<string, string> = {
  ave: "avenue", av: "avenue", st: "street", str: "street",
  blvd: "boulevard", rd: "road", dr: "drive",
};

export function normalize(q: string) {
  const tokens = q
    .toLowerCase()
    .replace(/#\s*\w+/g, " ")
    .replace(/[.,]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => ABBR[t] ?? t);
  return {
    number: tokens.find((t) => /^\d{1,5}$/.test(t)) ?? "",
    zip: tokens.find((t) => /^\d{5}$/.test(t)) ?? "",
    words: tokens.filter((t) => !/^\d+$/.test(t) && !["dallas", "tx", "texas"].includes(t)),
  };
}

export type Match = { parcel: Parcel; score: number };

export function matchParcels(q: string, parcels: Parcel[]): Match[] {
  if (!q.trim()) return [];
  const n = normalize(q);
  return parcels
    .map((parcel) => {
      const p = normalize(parcel.address);
      let score = 0;
      if (n.number && n.number === p.number) score += 40;
      if (p.words.length) {
        const hits = p.words.filter((w) =>
          n.words.some((x) => x === w || (x.length >= 4 && w.startsWith(x)))
        ).length;
        score += Math.round((40 * hits) / p.words.length);
      }
      if (n.zip && n.zip === parcel.zip) score += 20;
      else if (!n.zip) score += 10;
      return { parcel, score };
    })
    .filter((m) => m.score >= 50)
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
}