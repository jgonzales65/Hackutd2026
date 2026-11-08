"use client";
import { useCallback, useEffect, useState } from "react";
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

  const [bbox, setBbox] = useState("");
  const [loading, setLoading] = useState(true);
  const [truncated, setTruncated] = useState(false);
  const [retry, setRetry] = useState(0);
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);
  const onBoundsChange = useCallback((bounds: string) => setBbox(bounds), []);

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        const saved: unknown = JSON.parse(localStorage.getItem("watch") ?? "[]");
        if (Array.isArray(saved)) setWatch(saved.filter((id): id is string => typeof id === "string"));
      } catch {}
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!bbox) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/parcels?bbox=${encodeURIComponent(bbox)}`, { signal: controller.signal });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not load parcels.");
        if (!Array.isArray(data.parcels)) throw new Error("Invalid parcel response.");
        if (controller.signal.aborted) return;
        setParcels(data.parcels);
        setTruncated(data.truncated);
      } catch (err) {
        if (!controller.signal.aborted) {
          setParcels([]);
          setError(err instanceof Error ? err.message : "Could not load parcels.");
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [bbox, retry]);

  async function selectParcel(id: string) {
    const known = parcels.find(p => p.id === id);
    if (known) { setSelectedParcel(known); setSelectedId(id); return; }
    try {
      const response = await fetch(`/api/parcels?id=${encodeURIComponent(id)}`);
      const data = await response.json();
      if (!response.ok || !data.parcels?.length) throw new Error("Saved parcel could not be loaded.");
      setSelectedParcel(data.parcels[0]);
      setSelectedId(id);
    } catch { setError("Saved parcel could not be loaded. Please retry."); }
  }

  function toggleWatch(id: string) {
    const next = watch.includes(id) ? watch.filter((x) => x !== id) : [...watch, id];
    setWatch(next);
    try { localStorage.setItem("watch", JSON.stringify(next)); } catch {}
  }

  const selected = parcels.find((p) => p.id === selectedId) ?? selectedParcel;
  const mapParcels = selected && !parcels.some(p => p.id === selected.id) ? [...parcels, selected] : parcels;

  return (
    <div className="grid h-screen grid-rows-[auto_1fr]">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-line bg-panel px-4 py-2 print:hidden">
        <h1 className="font-serif text-xl font-semibold text-accent">Parcel Intelligence</h1>
        <SearchBar parcels={parcels} onPick={selectParcel} />
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
        <div className="grid min-h-0 grid-rows-[minmax(0,3fr)_minmax(0,2fr)] border-r border-line print:hidden">
          <div className="relative min-h-0">
            <ParcelMap parcels={mapParcels} selectedId={selectedId} minScore={minScore} onSelect={selectParcel} onBoundsChange={onBoundsChange} onError={setMapError} />
            <div role="status" aria-live="polite" className="absolute top-3 left-3 max-w-sm border border-line bg-panel px-3 py-2 text-sm">
              {loading ? "Loading real parcels…" : error ? <><span role="alert">{error}</span> <button className="underline" onClick={() => setRetry(n => n + 1)}>Retry</button></>
                : truncated ? "Showing 500 parcels. Zoom in to see more boundaries."
                : parcels.length ? `${parcels.length} real parcels in this view` : "No imported parcels in this view. Pan toward central Bexar County."}
              {mapError && <p role="alert">{mapError}</p>}
            </div>
            <p className="absolute bottom-6 left-3 flex gap-3 rounded-sm border border-line bg-panel px-3 py-1 text-xs">
              {[["#64748b", "Not assessed"], ["#5b7f67", "Low"], ["#b7791f", "Moderate"], ["#b5472b", "High"], ["#7a1f2b", "Critical"]].map(([c, t]) => (
                <span key={t} className="flex items-center gap-1">
                  <i className="inline-block h-2.5 w-2.5" style={{ background: c }} />{t}
                </span>
              ))}
            </p>
          </div>
          <ParcelTable parcels={parcels} selectedId={selectedId} minScore={minScore} onSelect={selectParcel} />
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
                        <button onClick={() => selectParcel(id)} className="w-full py-2 text-left text-accent hover:underline">
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

