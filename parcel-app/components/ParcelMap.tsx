"use client";
import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Parcel } from "@/lib/types";
import { centroid } from "@/lib/geo";

export default function ParcelMap({
  parcels, selectedId, minScore, onSelect, onBoundsChange, onError,
}: {
  onBoundsChange: (bbox: string) => void;
  onError: (message: string) => void;
  parcels: Parcel[];
  selectedId: string | null;
  minScore: number;
  onSelect: (id: string) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const onSelectRef = useRef(onSelect);
  const boundsRef = useRef(onBoundsChange);
  const errorRef = useRef(onError);
  const [ready, setReady] = useState(false);
  const lastFocused = useRef<string | null>(null);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);
  useEffect(() => { boundsRef.current = onBoundsChange; }, [onBoundsChange]);
  useEffect(() => { errorRef.current = onError; }, [onError]);

  // Create the map once
  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      center: [-98.4965, 29.4263],
      zoom: 13,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tileSize: 256,
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
            paint: {
              "raster-saturation": -1,
              "raster-contrast": -0.25,
              "raster-brightness-min": 0.2,
              "raster-brightness-max": 0.92,
            },
          },
        ],
      },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    mapRef.current = map;
    const reportBounds = () => {
      const b = map.getBounds();
      boundsRef.current([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].join(","));
    };
    map.on("moveend", reportBounds);
    map.on("error", () => errorRef.current("A map resource could not load. Check your network connection."));

    map.on("load", () => {
      // Parcels
      map.addSource("parcels", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "parcels-fill",
        type: "fill",
        source: "parcels",
        paint: {
          "fill-opacity": 0.78,
          "fill-color": ["case", ["<", ["coalesce", ["get", "score"], -1], 0], "#64748b", ["step", ["get", "score"], "#8d9d90", 30, "#b48a2c", 60, "#d9381e", 80, "#5a1409"]],
        },
      });
      map.addLayer({
        id: "parcels-line",
        type: "line",
        source: "parcels",
        paint: { "line-color": "#f8f7f3", "line-width": 1 },
      });
      map.addLayer({
        id: "parcels-selected",
        type: "line",
        source: "parcels",
        filter: ["==", ["get", "id"], ""],
        paint: { "line-color": "#141414", "line-width": 3 },
      });

      // Listing pin drift (wrong pin and dashed line to the verified parcel)
      map.addSource("drift", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "drift-line",
        type: "line",
        source: "drift",
        filter: ["==", ["geometry-type"], "LineString"],
        paint: { "line-color": "#d9381e", "line-width": 2, "line-dasharray": [2, 2] },
      });
      map.addLayer({
        id: "drift-pin",
        type: "circle",
        source: "drift",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-radius": 7,
          "circle-color": "#d9381e",
          "circle-stroke-color": "#f8f7f3",
          "circle-stroke-width": 2,
        },
      });

      map.on("click", "parcels-fill", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (id) onSelectRef.current(id);
      });
      map.on("mouseenter", "parcels-fill", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "parcels-fill", () => (map.getCanvas().style.cursor = ""));
      setReady(true);
      reportBounds();
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Load parcel data
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource("parcels") as maplibregl.GeoJSONSource).setData({
      type: "FeatureCollection" as const,
      features: parcels.map((p) => ({
        type: "Feature" as const,
        geometry: p.geometry ?? { type: "Polygon" as const, coordinates: p.coordinates },
        properties: { id: p.id, score: p.score },
      })),
    });
  }, [parcels, ready]);

  // Risk filter
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const f: maplibregl.FilterSpecification = minScore === 0 ? ["all"] : [">=", ["coalesce", ["get", "score"], -1], minScore];
    map.setFilter("parcels-fill", f);
    map.setFilter("parcels-line", f);
  }, [minScore, ready]);

  // Highlight and fly to the selected parcel
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    map.setFilter("parcels-selected", ["==", ["get", "id"], selectedId ?? ""]);
    const p = parcels.find((x) => x.id === selectedId);
    if (p && lastFocused.current !== selectedId) {
      lastFocused.current = selectedId;
      map.flyTo({ center: centroid(p), zoom: 16.5, duration: 800 });
    }
  }, [selectedId, parcels, ready]);

  // Show the wrong listing pin for the selected parcel
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const p = parcels.find((x) => x.id === selectedId);
    const features: GeoJSON.Feature[] = [];
    if (p?.listingPin) {
      features.push(
        { type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p.listingPin } },
        { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [p.listingPin, centroid(p)] } }
      );
    }
    (map.getSource("drift") as maplibregl.GeoJSONSource).setData({ type: "FeatureCollection", features });
  }, [selectedId, parcels, ready]);

  return <div ref={container} className="h-full w-full" />;
}
