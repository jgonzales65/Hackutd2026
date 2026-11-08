"use client";
import { useState } from "react";
import { matchParcels } from "@/lib/match";
import type { Parcel } from "@/lib/types";

export default function SearchBar({ parcels, onPick }: { parcels: Parcel[]; onPick: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const matches = matchParcels(q, parcels);
  const pick = (id: string) => { onPick(id); setOpen(false); };

  return (
    <div className="relative w-full max-w-md">
      <form onSubmit={(e) => { e.preventDefault(); if (matches[0]) pick(matches[0].parcel.id); setOpen(true); }}>
        <input
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          placeholder="Search by address, e.g. 1420 McKinney Ave"
          aria-label="Search by address"
          className="w-full rounded-sm border border-line bg-panel px-3 py-1.5"
        />
      </form>
      {open && q.trim() && (
        <ul className="absolute z-10 mt-1 w-full rounded-sm border border-line bg-panel">
          {matches.length === 0 ? (
            <li className="p-3 text-sm text-soft">No confident match. Try adding the street name or number.</li>
          ) : (
            matches.map((m) => (
              <li key={m.parcel.id} className="border-b border-line last:border-0">
                <button onClick={() => pick(m.parcel.id)} className="flex w-full justify-between gap-3 p-3 text-left hover:bg-paper">
                  <span>{m.parcel.address}<span className="block text-sm text-soft">{m.parcel.id}, {m.parcel.zip}</span></span>
                  <span className="text-sm text-soft">{m.score >= 80 ? "Strong match" : "Possible match"} ({m.score}%)</span>
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}