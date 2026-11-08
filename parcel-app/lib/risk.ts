import type { Parcel } from "./types";

export const RAMP = ["#8d9d90", "#b48a2c", "#d9381e", "#5a1409"];

export function level(score: number | null) {
  if (score === null) return { label: "Not assessed", color: "#64748b" };
  if (score >= 80) return { label: "Critical", color: RAMP[3] };
  if (score >= 60) return { label: "High", color: RAMP[2] };
  if (score >= 30) return { label: "Moderate", color: RAMP[1] };
  return { label: "Low", color: RAMP[0] };
}

export function verdict(p: Parcel) {
  if (p.score === null) return "Overall risk has not been assessed. Missing information does not establish absence of risk.";
  const lv = level(p.score).label;
  const top = p.findings[0];
  if (!top) return `${lv} risk. We found nothing that should hold up a purchase.`;
  const n = p.findings.length;
  const t = top.text.charAt(0).toLowerCase() + top.text.slice(1);
  return `${lv} risk. ${n} issue${n > 1 ? "s" : ""} to sort out before closing, starting with: ${t}.`;
}