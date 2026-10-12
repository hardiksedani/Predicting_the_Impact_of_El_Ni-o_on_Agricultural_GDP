"use client";

import { useMemo } from "react";
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from "react-simple-maps";
import { scaleLinear } from "d3-scale";
import { states, type StateCollection } from "vardhan-maps/data";
import type { Position } from "geojson";

// react-simple-maps uses D3's spherical winding convention, opposite to the
// mixed ring directions in the bundled GeoJSON. Orient each polygon separately
// so multipart states fill their actual land instead of the area outside India.
function orientPolygon(rings: Position[][]): Position[][] {
  const outer = rings[0];
  const signedArea = outer.reduce((sum, point, index) => {
    const next = outer[(index + 1) % outer.length];
    return sum + point[0] * next[1] - next[0] * point[1];
  }, 0);
  return signedArea > 0 ? rings.map((ring) => [...ring].reverse()) : rings;
}

const mapGeography: StateCollection = {
  ...states,
  features: states.features.map((feature) => ({
    ...feature,
    geometry:
      feature.geometry.type === "Polygon"
        ? {
            ...feature.geometry,
            coordinates: orientPolygon(feature.geometry.coordinates),
          }
        : {
            ...feature.geometry,
            coordinates: feature.geometry.coordinates.map((polygon) =>
              orientPolygon(polygon),
            ),
          },
  })),
};

/** Map GeoJSON state names to our dataset names where they differ. */
const STATE_NAME_MAP: Record<string, string> = {
  "NCT of Delhi": "Delhi",
  "Andaman and Nicobar": "Andaman and Nicobar Islands",
  "Andaman and Nicobar Islands": "Andaman and Nicobar Islands",
  "Jammu and Kashmir": "Jammu & Kashmir",
  "Dadra and Nagar Haveli and Daman and Diu": "Dadra and Nagar Haveli",
  Telangana: "Telangana",
};

interface Props {
  /** State name → latest crop-GSVA deviation from that state's historical mean (%). */
  impactByState: Record<string, number>;
  onStateClick?: (state: string) => void;
  selectedState?: string;
}

export default function IndiaChoropleth({
  impactByState,
  onStateClick,
  selectedState,
}: Props) {
  const values = Object.values(impactByState);
  const colorScale = useMemo(() => {
    const min = values.length ? Math.min(...values, -30) : -30;
    const max = values.length ? Math.max(...values, 10) : 10;
    return scaleLinear<string>()
      .domain([min, 0, max])
      .range(["#b91c1c", "#22c55e", "#15803d"]);
  }, [values]);

  return (
    <div>
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ scale: 900, center: [82, 23] }}
        width={700}
        height={600}
        className="mx-auto w-full max-w-3xl"
      >
        <ZoomableGroup center={[82, 23]} zoom={1}>
          <Geographies geography={mapGeography}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const rawName =
                  geo.properties.name ??
                  geo.properties.ST_NM ??
                  geo.properties.NAME_1 ??
                  "";
                const mappedName = STATE_NAME_MAP[rawName] ?? rawName;
                const impact = impactByState[mappedName];
                const fill =
                  impact !== undefined ? colorScale(impact) : "#e2e8f0";
                const isSelected = selectedState === mappedName;

                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill={fill}
                    stroke={isSelected ? "#1e3a5f" : "#fff"}
                    strokeWidth={isSelected ? 1.5 : 0.5}
                    style={{
                      default: { outline: "none" },
                      hover: { outline: "none", opacity: 0.85, cursor: "pointer" },
                      pressed: { outline: "none" },
                    }}
                    onClick={() => {
                      if (impact !== undefined && onStateClick) {
                        onStateClick(mappedName);
                      }
                    }}
                  />
                );
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>
      <div className="mt-3 flex flex-wrap items-center justify-center gap-4 text-xs text-slate-600">
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-6 rounded bg-[#b91c1c]" />
          Below state crop-GSVA mean
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-3 w-6 rounded bg-[#22c55e]" />
          At or above state crop-GSVA mean
        </span>
        <span className="text-slate-400">Click a highlighted state to select</span>
      </div>
      <p className="mt-2 text-center text-xs text-slate-500">
        Illustrative boundaries, not an official map. Map data: {" "}
        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline">
          © OpenStreetMap contributors
        </a>.
      </p>
    </div>
  );
}
