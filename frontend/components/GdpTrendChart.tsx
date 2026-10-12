"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { HistoryRow } from "@/lib/api";

interface Props {
  history: HistoryRow[];
}

export default function GdpTrendChart({ history }: Props) {
  const chartData = history.map((row) => ({
    year: row.year,
    gdp: row.agricultural_gdp_cr,
    oni: row.oni_index,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="year" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="gdp"
            tick={{ fontSize: 12 }}
            label={{ value: "Crop GSVA (₹ crore)", angle: -90, position: "insideLeft", fontSize: 11 }}
          />
          <YAxis
            yAxisId="oni"
            orientation="right"
            tick={{ fontSize: 12 }}
            label={{ value: "ONI", angle: 90, position: "insideRight", fontSize: 11 }}
          />
          <Tooltip
            formatter={(value, name) => {
              if (typeof value !== "number") return [String(value), name];
              if (name === "gdp") return [`₹${value.toFixed(1)} crore`, "Crop GSVA"];
              return [value.toFixed(2), "ONI Index"];
            }}
          />
          <Legend />
          <Line
            yAxisId="gdp"
            type="monotone"
            dataKey="gdp"
            name="Crop GSVA"
            stroke="#1e3a5f"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
          <Line
            yAxisId="oni"
            type="monotone"
            dataKey="oni"
            name="ONI Index"
            stroke="#d97706"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
