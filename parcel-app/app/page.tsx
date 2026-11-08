"use client";
import { useEffect, useState } from "react";
import ParcelMap from "@/components/ParcelMap";
import ParcelTable from "@/components/ParcelTable";
import Scorecard from "@/components/Scorecard";
import SearchBar from "@/components/SearchBar";
import type { Parcel } from "@/lib/types";

export default function Home() {
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [minScore, setMinScore] = useState(0);
  const [watch, setWatch] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/parcels").then((r) => r.json()).then(setParcels)
      .catch(() => setError("Could not load parcels."));
    try { setWatch(JSON.parse(localStorage.getItem("watch") ?? "[]")); } catch {}
  }, []);

  function toggleWatch(id: string) {
    const next = watch.includes(id) ? watch.filter((x) => x !== id) : [...watch, id];
    setWatch(next);
    try { localStorage.setItem("watch", JSON.stringify(next)); } catch {}
  }

  const selected = parcels.find((p) => p.id === selectedId) ?? null;

  return (
    <div className="grid h-screen grid-rows-[auto_1fr]">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-line bg-panel px-4 py-2 print:hidden">
        <h1 className="font-serif text-xl font-semibold text-accent">Parcel Intelligence</h1>
        <SearchBar parcels={parcels} onPick={setSelectedId} />
        <label className="ml-auto flex items-center gap-2 text-sm">
          Show
          <select value={minScore} onChange={(e) => setMinScore(+e.target.value)}
            className="rounded-sm border border-line bg-panel px-2 py-1">
            <option value={0}>All parcels</option>
            <option value={30}>Moderate risk and above</option>
            <option value={60}>High risk and above</option>
          </select>
        </label>
      </header>

      <main className="grid min-h-0 grid-cols-[1fr_440px] print:block">
        <div className="grid min-h-0 grid-rows-[3fr_2fr] border-r border-line print:hidden">
          <div className="relative min-h-0">
            <ParcelMap parcels={parcels} selectedId={selectedId} minScore={minScore} onSelect={setSelectedId} />
            <p className="absolute bottom-6 left-3 flex gap-3 rounded-sm border border-line bg-panel px-3 py-1 text-xs">
              {[["#5b7f67", "Low"], ["#b7791f", "Moderate"], ["#b5472b", "High"], ["#7a1f2b", "Critical"]].map(([c, t]) => (
                <span key={t} className="flex items-center gap-1">
                  <i className="inline-block h-2.5 w-2.5" style={{ background: c }} />{t}
                </span>
              ))}
            </p>
          </div>
          <ParcelTable parcels={parcels} selectedId={selectedId} minScore={minScore} onSelect={setSelectedId} />
        </div>

        <aside className="min-h-0 overflow-y-auto bg-panel p-6 print:p-0">
          {error ? <p className="text-high">{error}</p> : (
            <>
              <Scorecard parcel={selected} watched={selected ? watch.includes(selected.id) : false}
                onToggleWatch={() => selected && toggleWatch(selected.id)} />
              {watch.length > 0 && (
                <section className="print:hidden">
                  <h3 className="mt-8 border-b border-line pb-1 text-sm font-semibold">Your watchlist</h3>
                  <ul className="text-sm">
                    {watch.map((id) => (
                      <li key={id} className="border-b border-line">
                        <button onClick={() => setSelectedId(id)} className="w-full py-2 text-left text-accent hover:underline">
                          {parcels.find((x) => x.id === id)?.address ?? id}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </aside>
      </main>
    </div>
  );
}

