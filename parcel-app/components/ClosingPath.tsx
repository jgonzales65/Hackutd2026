"use client";
import { useState } from "react";
import type { Parcel } from "@/lib/types";

const money = (n: number) => "$" + n.toLocaleString();

export default function ClosingPath({ parcel }: { parcel: Parcel }) {
  const [chosen, setChosen] = useState<string[]>([]);
  const steps = parcel.findings.filter((f) => f.cure);
  if (steps.length === 0 || parcel.score === null) return null;

  const picked = steps.filter((f) => chosen.includes(f.text));
  const cost = picked.reduce((a, f) => a + f.cure!.cost, 0);
  const days = 21 + (picked.length ? Math.max(...picked.map((f) => f.cure!.days)) : 0);
  const after = Math.max(0, parcel.score - picked.reduce((a, f) => a + f.cure!.reduces, 0));
  const toggle = (t: string) => setChosen((c) => (c.includes(t) ? c.filter((x) => x !== t) : [...c, t]));

  return (
    <section>
      <h3 className="mt-8 border-b border-line pb-1 text-sm font-semibold">If you want to fix it first</h3>
      <ul className="text-sm">
        {steps.map((f) => (
          <li key={f.text} className="border-b border-line">
            <label className="flex cursor-pointer gap-3 py-2">
              <input type="checkbox" checked={chosen.includes(f.text)} onChange={() => toggle(f.text)} />
              <span>
                {f.cure!.label}
                <span className="block text-soft">About {f.cure!.days} days and {money(f.cure!.cost)}</span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-sm">
        {picked.length === 0
          ? <span className="text-soft">Tick a step to see how it changes the risk, the timeline and the cost.</span>
          : <>Doing {picked.length === steps.length ? "all of these" : "these"} brings the risk from {parcel.score} to {after}, with closing in about {days} days and {money(cost)} in cure costs. These are estimates, not quotes.</>}
      </p>
    </section>
  );
}