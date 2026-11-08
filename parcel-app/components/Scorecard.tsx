import type { Parcel } from "@/lib/types";
import { level, verdict, displayScore } from "@/lib/risk";
import LocationProof from "./LocationProof";
import ClosingPath from "./ClosingPath";
import PlatDrawing from "./PlatDrawing";

const LABELS = {
  flood: "Flood (FEMA)",
  environmental: "Other environmental hazards",
  financial: "Financial / property",
  title: "Title and liens",
  permits: "Permits",
  zoning: "Zoning",
} as const;

const head = "mt-10 border-b border-line pb-1 font-serif text-xl italic";

function Stamp({ score }: { score: number | null }) {
  const { label: text, color } = level(score);
  return (
    <span
      className="inline-block shrink-0 -rotate-3 border-2 px-2 py-1 text-center text-xs font-bold uppercase leading-tight tracking-widest"
      style={{ color, borderColor: color }}
    >
      {text}
    </span>
  );
}

export default function Scorecard({
  parcel,
  watched,
  onToggleWatch,
}: {
  parcel: Parcel | null;
  watched: boolean;
  onToggleWatch: () => void;
}) {
  if (!parcel) {
    return (
      <div>
        <h2 className="font-serif text-4xl italic leading-tight">
          Know the ground before you buy it.
        </h2>
        <p className="mt-3 text-soft">
          Search an address or choose a parcel. We confirm where it really is, then tell you
          what could hold up the sale.
        </p>
      </div>
    );
  }

  const score = displayScore(parcel);
  const lv = level(score);

  return (
    <article>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-soft">
            File no. {parcel.id} · ZIP {parcel.zip || "unavailable"}
          </p>
          <h2 className="font-serif text-4xl leading-none">{parcel.address}</h2>
          <p className="mt-1 text-soft">Record owner: {parcel.owner}</p>
        </div>
        <Stamp score={score} />
      </div>

      <PlatDrawing parcel={parcel} />

      <div className="mt-4 flex items-baseline gap-3">
        <span className="font-serif text-8xl leading-none tabular-nums">{score ?? "—"}</span>
        <span className="text-soft">{score === null ? "Not assessed" : parcel.score === null ? "Flood severity / 100" : "Overall / 100"}</span>
        <span className="ml-auto flex items-center gap-2 font-medium">
          <i
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: lv.color }}
          />
          {lv.label}{score === null ? "" : parcel.score === null ? " flood severity" : " risk"}
        </span>
      </div>
      <p className="mt-3 leading-relaxed">{verdict(parcel)}</p>

      <h3 className={head}>Risk by category</h3>
      <ul className="text-sm">
        {(Object.keys(LABELS) as (keyof typeof LABELS)[]).map((k) => (
          <li key={k} className="flex items-center gap-3 border-b border-line py-2">
            <span className="flex-1">{LABELS[k]}</span>
            <span className="h-1 w-24 bg-line">
              <span
                className="block h-1"
                style={{
                  width: `${parcel.breakdown[k] ?? 0}%`,
                  background: level(parcel.breakdown[k]).color,
                }}
              />
            </span>
            <span className="w-6 text-right tabular-nums">{parcel.breakdown[k] ?? "—"}</span>
          </li>
        ))}
      </ul>

      {parcel.assessment && <div className="mt-3 text-sm text-soft">
        <p>Overall risk: not assessed. Missing assessments: {parcel.assessment.missingCategories.join(", ")}.</p>
        <p>Method: {parcel.assessment.method} · {parcel.assessment.status.replaceAll("_", " ")}</p>
        <p>Preliminary application severity index. Not an official FEMA or insurance rating, probability, or loss estimate.</p>
      </div>}
      <h3 className={head}>Verified findings</h3>
      {parcel.findings.length === 0 ? (
        <p className="py-2 text-sm text-soft">No title or permit assessment available.</p>
      ) : (
        parcel.findings.map((f) => (
          <div key={f.text} className="border-b border-line py-3">
            <p className="font-medium">{f.text}</p>
            <p className="text-sm text-soft">
              {f.confidence} confidence · {f.source}
            </p>
            <p className="mt-1 text-sm">{f.impact}</p>
            {f.snippet && (
              <details className="mt-1 text-sm">
                <summary className="cursor-pointer text-accent">See the document text</summary>
                <blockquote className="mt-1 border-l-2 border-line pl-3 font-serif italic text-soft">
                  {f.snippet}
                </blockquote>
              </details>
            )}
          </div>
        ))
      )}

      {parcel.flood && <section>
        <h3 className={head}>FEMA mapped flood zones</h3>
        <p className="mt-2 text-sm">{!parcel.flood.available ? "Flood data unavailable."
          : parcel.flood.matches.length === 0 ? "No match in the pilot dataset. Flood overlap is unknown."
          : "Mapped zone intersections found. Pilot coverage is incomplete."}</p>
        {parcel.flood.matches.map((m, i) => <div key={i} className="border-b border-line py-2 text-sm">
          <p>Zone {m.zone}{m.subtype ? ` · ${m.subtype}` : ""}</p>
          <p>{m.sfha === true ? "Special Flood Hazard Area overlap confirmed." : "This zone alone does not confirm a Special Flood Hazard Area overlap."}</p>
          <a href={m.source} target="_blank" rel="noreferrer" className="text-accent underline">FEMA NFHL · {m.citation || "source"}</a>
          <p className="text-soft">Retrieved: {new Date(m.retrievedAt).toLocaleDateString()}</p>
        </div>)}
        <p className="mt-2 text-xs text-soft">Boundary contact counts as intersection. Missing matches do not mean no flood risk. No probability or financial loss is estimated.</p>
      </section>}
      <LocationProof parcel={parcel} />
      <ClosingPath key={parcel.id} parcel={parcel} />

      <div className="mt-10 flex gap-2 print:hidden">
        <button
          onClick={() => window.print()}
          className="bg-ink px-4 py-2 font-medium text-white"
        >
          Print closing file
        </button>
        <button onClick={onToggleWatch} className="border border-line bg-panel px-4 py-2">
          {watched ? "Remove from watchlist" : "Add to watchlist"}
        </button>
      </div>
    </article>
  );
}