"use client";
import { useState } from "react";
import type { Parcel } from "@/lib/types";
import { level } from "@/lib/risk";

export default function ParcelTable({
  parcels, selectedId, minScore, onSelect,
}: {
  parcels: Parcel[];
  selectedId: string | null;
  minScore: number;
  onSelect: (id: string) => void;
}) {
  const [asc, setAsc] = useState(false);
  const rows = parcels
    .filter((p) => p.score >= minScore)
    .sort((a, b) => (asc ? a.score - b.score : b.score - a.score));

  return (
    <div className="flex h-full flex-col bg-panel">
      <div className="flex items-baseline justify-between border-b border-line px-4 py-2">
        <h2 className="font-serif text-lg font-semibold">Parcels</h2>
        <span className="text-sm text-soft">{rows.length} shown</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-panel text-soft">
            <tr className="border-b border-line">
              <th className="px-4 py-2 font-medium">Address</th>
              <th className="px-2 py-2 font-medium">Owner</th>
              <th className="px-2 py-2 font-medium">
                <button onClick={() => setAsc(!asc)} className="font-medium">
                  Risk {asc ? "↑" : "↓"}
                </button>
              </th>
              <th className="px-2 py-2 font-medium">Main issue</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => {
              const lv = level(p.score);
              return (
                <tr
                  key={p.id}
                  tabIndex={0}
                  onClick={() => onSelect(p.id)}
                  onKeyDown={(e) => e.key === "Enter" && onSelect(p.id)}
                  className={`cursor-pointer border-b border-line hover:bg-paper ${p.id === selectedId ? "bg-paper font-medium" : ""}`}
                >
                  <td className="px-4 py-2">{p.address}</td>
                  <td className="px-2 py-2 text-soft">{p.owner}</td>
                  <td className="px-2 py-2 whitespace-nowrap">
                    <i className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: lv.color }} />
                    <span className="tabular-nums">{p.score}</span> {lv.label}
                  </td>
                  <td className="px-2 py-2 text-soft">{p.findings[0]?.text ?? "None found"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}