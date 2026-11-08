import type { Parcel } from "@/lib/types";
import { level, verdict } from "@/lib/risk";
import LocationProof from "./LocationProof";
import ClosingPath from "./ClosingPath";
import PlatDrawing from "./PlatDrawing";

const LABELS = {
  flood: "Flood and environment",
  title: "Title and liens",
  permits: "Permits",
  zoning: "Zoning",
} as const;

const head = "mt-10 border-b border-line pb-1 font-serif text-xl italic";

function Stamp({ score }: { score: number }) {
  const [text, color] =
    score < 30 ? ["Clear to close", "#8d9d90"]
    : score < 60 ? ["Conditions apply", "#b48a2c"]
    : score < 80 ? ["Hold: cure first", "#d9381e"]
    : ["Do not proceed", "#5a1409"];
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

  const lv = level(parcel.score);

  return (
    <article>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-soft">
            File no. {parcel.id} · ZIP {parcel.zip}
          </p>
          <h2 className="font-serif text-4xl leading-none">{parcel.address}</h2>
          <p className="mt-1 text-soft">Record owner: {parcel.owner}</p>
        </div>
        <Stamp score={parcel.score} />
      </div>

      <PlatDrawing parcel={parcel} />

      <div className="mt-4 flex items-baseline gap-3">
        <span className="font-serif text-8xl leading-none tabular-nums">{parcel.score}</span>
        <span className="text-soft">out of 100</span>
        <span className="ml-auto flex items-center gap-2 font-medium">
          <i
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ background: lv.color }}
          />
          {lv.label} risk
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
                  width: `${parcel.breakdown[k]}%`,
                  background: level(parcel.breakdown[k]).color,
                }}
              />
            </span>
            <span className="w-6 text-right tabular-nums">{parcel.breakdown[k]}</span>
          </li>
        ))}
      </ul>

      <h3 className={head}>Exceptions to clear title</h3>
      {parcel.findings.length === 0 ? (
        <p className="py-2 text-sm text-soft">Nothing above the alert level.</p>
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