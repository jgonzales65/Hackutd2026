/** Preliminary application severity index; never a probability or FEMA rating. */
export const FLOOD_METHOD = 'fema-zone-severity-v1';
export type FloodMatch = {
  zone: string; subtype: string | null; sfha: boolean | null;
  source: string; citation: string | null; retrievedAt: string;
};

function zoneScore(match: FloodMatch): number | null {
  const zone = match.zone.trim().toUpperCase();
  const subtype = (match.subtype ?? '').trim().toUpperCase();
  if (match.sfha === true && (subtype === 'FLOODWAY' || /^(V|VE|V\d+)$/.test(zone))) return 90;
  if (match.sfha === true && /^(A|AE|AO|AH|A99|AR|A\d+|AR\/.+)$/.test(zone)) return 65;
  if (zone === 'X' && match.sfha === false &&
      ['0.2 PCT ANNUAL CHANCE FLOOD HAZARD', '1 PCT FUTURE CONDITIONS'].includes(subtype)) return 35;
  if (zone === 'X' && match.sfha === false && subtype === 'AREA OF MINIMAL FLOOD HAZARD') return 10;
  return null;
}

export function assessFlood(matches: FloodMatch[], available: boolean, parcelCovered: boolean) {
  const scored = matches.map(match => ({ ...match, score: zoneScore(match) }));
  const known = scored.filter(m => m.score !== null);
  const maximum = known.length ? Math.max(...known.map(m => m.score!)) : null;
  // A positive hazard is usable as a severity floor. Low requires complete mapped
  // parcel geometry and no unrecognized intersecting zone. Regional coverage stays partial.
  const score = available && maximum !== null && (maximum >= 25 ||
    (parcelCovered && known.length === matches.length)) ? maximum : null;
  const status = !available ? 'data_unavailable' : score === null ? 'insufficient_coverage'
    : parcelCovered && known.length === matches.length ? 'mapped_parcel_assessed' : 'minimum_observed_severity';
  return {
    score, method: FLOOD_METHOD, status, parcelCovered, regionalCoverageComplete: false,
    scope: 'flood_only' as const,
    explanation: score === null
      ? 'Insufficient mapped flood evidence to assign a score. No match or partial minimal-hazard coverage does not establish low risk.'
      : `Highest recognized intersecting FEMA zone severity is ${score}/100. ` +
        (status === 'minimum_observed_severity' ? 'Partial or unrecognized coverage: this is a minimum observed severity; higher hazards may be missing.'
          : 'Imported FEMA polygons cover the whole parcel geometry; regional pilot coverage remains incomplete.'),
    evidence: scored,
    missingCategories: ['environmental', 'financial', 'ownership/title', 'permits', 'zoning'],
  };
}
