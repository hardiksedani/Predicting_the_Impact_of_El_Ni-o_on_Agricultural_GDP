"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MODEL_LABELS, MODEL_NAMES } from "@/lib/constants";
import { ModelComparison } from "@/lib/api";

interface Props {
  data: ModelComparison;
  metric?: "mae" | "rmse" | "r2";
}

export default function ModelComparisonChart({ data, metric = "rmse" }: Props) {
  const chartData = MODEL_NAMES.filter((name) => data.models && data.models[name]).map((name) => ({
    model: MODEL_LABELS[name] || name,
    mae: data.models[name].mae,
    rmse: data.models[name].rmse,
    r2: data.models[name].r2,
  }));

  const labels: Record<string, string> = {
    mae: "MAE (₹ crore)",
    rmse: "RMSE (₹ crore)",
    r2: "R²",
  };

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="model" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value) => [
              typeof value === "number" ? value.toFixed(2) : String(value),
              labels[metric],
            ]}
          />
          <Legend />
          <Bar dataKey={metric} fill="#1e3a5f" name={labels[metric]} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ModelMetricsGroupedChart({ data }: { data: ModelComparison }) {
  const chartData = MODEL_NAMES.filter((name) => data.models && data.models[name]).map((name) => ({
    model: MODEL_LABELS[name] || name,
    MAE: data.models[name].mae,
    RMSE: data.models[name].rmse,
    "R²": data.models[name].r2,
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="model" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="MAE" fill="#1e3a5f" radius={[2, 2, 0, 0]} />
          <Bar dataKey="RMSE" fill="#334155" radius={[2, 2, 0, 0]} />
          <Bar dataKey="R²" fill="#64748b" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
