import type { Parcel } from "@/lib/types";
import { level } from "@/lib/risk";

export default function PlatDrawing({ parcel }: { parcel: Parcel }) {
  // Corners of the parcel (the last point repeats the first, so drop it)
  const ring = parcel.coordinates[0].slice(0, -1) as [number, number][];
  const n = ring.length;
  const all: [number, number][] = parcel.listingPin ? [...ring, parcel.listingPin] : ring;

  // Convert longitude/latitude into meters, with the top-left as the origin
  const lng0 = Math.min(...all.map((p) => p[0]));
  const lat0 = Math.max(...all.map((p) => p[1]));
  const k = Math.cos((lat0 * Math.PI) / 180) * 111320;
  const pts: [number, number][] = all.map((p) => [(p[0] - lng0) * k, (lat0 - p[1]) * 110540]);

  // Scale to fit the drawing
  const W = 340, H = 190, pad = 40;
  const maxX = Math.max(...pts.map((p) => p[0])) || 1;
  const maxY = Math.max(...pts.map((p) => p[1])) || 1;
  const s = Math.min((W - 2 * pad) / maxX, (H - 2 * pad) / maxY);
  const P: [number, number][] = pts.map(([x, y]) => [pad + x * s, pad + y * s]);

  const poly = P.slice(0, n);
  const pin = parcel.listingPin ? P[n] : null;
  const cx = poly.reduce((a, p) => a + p[0], 0) / n;
  const cy = poly.reduce((a, p) => a + p[1], 0) / n;

  // Push a label point outward from the center of the parcel
  const out = (x: number, y: number, d: number): [number, number] => {
    const dx = x - cx, dy = y - cy, len = Math.hypot(dx, dy) || 1;
    return [x + (dx / len) * d, y + (dy / len) * d];
  };
  const feet = (a: number, b: number) =>
    Math.round(Math.hypot(pts[a][0] - pts[b][0], pts[a][1] - pts[b][1]) * 3.281);
  const color = level(parcel.score).color;

  return (
    <figure className="mt-4">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full border border-line bg-paper"
        role="img"
        aria-label={`Boundary drawing of ${parcel.address}`}
      >
        {/* Parcel boundary */}
        <polygon
          points={poly.map((p) => p.join(",")).join(" ")}
          fill={color}
          fillOpacity={0.16}
          stroke="#141414"
          strokeWidth={1.5}
          strokeDasharray="6 3"
        />

        {/* Corner points, lettered A, B, C, D */}
        {poly.map((p, i) => {
          const [lx, ly] = out(p[0], p[1], 13);
          return (
            <g key={i}>
              <circle cx={p[0]} cy={p[1]} r={3} fill="#141414" />
              <text x={lx} y={ly + 3} fontSize={10} textAnchor="middle" fill="#141414" fontWeight={600}>
                {String.fromCharCode(65 + i)}
              </text>
            </g>
          );
        })}

        {/* Side lengths in feet */}
        {poly.map((p, i) => {
          const q = poly[(i + 1) % n];
          const [lx, ly] = out((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 14);
          return (
            <text key={`d${i}`} x={lx} y={ly + 3} fontSize={9.5} textAnchor="middle" fill="#6d6a63">
              {feet(i, (i + 1) % n)} ft
            </text>
          );
        })}

        {/* The wrong listing pin, if there is one */}
        {pin && (
          <g>
            <line x1={pin[0]} y1={pin[1]} x2={cx} y2={cy} stroke="#d9381e" strokeDasharray="3 3" />
            <path
              d={`M${pin[0] - 5} ${pin[1] - 5}l10 10m0 -10l-10 10`}
              stroke="#d9381e"
              strokeWidth={2}
            />
            <text x={pin[0]} y={pin[1] - 9} fontSize={9.5} textAnchor="middle" fill="#d9381e">
              Listing pin
            </text>
          </g>
        )}

        <text x={W - 14} y={20} fontSize={11} textAnchor="middle" fill="#6d6a63">
          N↑
        </text>
      </svg>
      <figcaption className="mt-1 text-xs text-soft">
        Boundary drawn from county record geometry. Not a survey.
      </figcaption>
    </figure>
  );
}