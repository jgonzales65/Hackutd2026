import type { Parcel } from "./types";

export const RAMP = ["#8d9d90", "#b48a2c", "#d9381e", "#5a1409"];

export function level(score: number | null) {
  if (score === null) return { label: "Not assessed", color: "#64748b" };
  if (score >= 75) return { label: "Critical", color: RAMP[3] };
  if (score >= 50) return { label: "High", color: RAMP[2] };
  if (score >= 25) return { label: "Moderate", color: RAMP[1] };
  return { label: "Low", color: RAMP[0] };
}

export function displayScore(p: Parcel) {
  return p.score ?? p.assessment?.score ?? null;
}

export function verdict(p: Parcel) {
  if (p.score === null) return p.assessment?.score != null
    ? `${level(p.assessment.score).label} mapped flood severity. Flood-only assessment; overall property risk remains unassessed. ${p.assessment.explanation}`
    : "Overall and flood risk remain unassessed. Missing information does not establish absence of risk.";
  const lv = level(p.score).label;
  const top = p.findings[0];
  if (!top) return `${lv} risk. We found nothing that should hold up a purchase.`;
  const n = p.findings.length;
  const t = top.text.charAt(0).toLowerCase() + top.text.slice(1);
  return `${lv} risk. ${n} issue${n > 1 ? "s" : ""} to sort out before closing, starting with: ${t}.`;
}