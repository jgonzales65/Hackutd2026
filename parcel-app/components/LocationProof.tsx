import type { Parcel } from "@/lib/types";
import { centroid, meters } from "@/lib/geo";
import { normalize } from "@/lib/match";

const key = (s: string) => { const n = normalize(s); return n.number + n.words.join(" "); };

export default function LocationProof({ parcel }: { parcel: Parcel }) {
  if (!parcel.records) return null;
  const truth = key(parcel.address);
  const drift = parcel.listingPin ? Math.round(meters(parcel.listingPin, centroid(parcel))) : null;
  return (
    <section>
      <h3 className="mt-8 border-b border-line pb-1 text-sm font-semibold">Does the address check out?</h3>
      <ul className="text-sm">
        {parcel.records.map((r) => {
          const ok = key(r.value) === truth;
          return (
            <li key={r.source} className="flex justify-between gap-3 border-b border-line py-2">
              <span>{r.source}: {r.value}</span>
              <span className={ok ? "text-low" : "text-high"}>{ok ? "Matches" : "Doesn’t match"}</span>
            </li>
          );
        })}
      </ul>
      {drift !== null && (
        <p className={`mt-2 text-sm ${drift > 15 ? "text-high" : "text-low"}`}>
          {drift > 15
            ? `The listing’s map pin is ${drift} m away from the verified parcel (shown on the map with a dashed line).`
            : "The listing’s map pin sits on the verified parcel."}
        </p>
      )}
    </section>
  );
}