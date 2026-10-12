"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { MODEL_LABELS, ModelName } from "@/lib/constants";
import type { LinearClimatePermutation } from "@/lib/api";

const FEATURE_LABELS: Record<string, string> = {
  rainfall_mm: "Rainfall (mm)",
  avg_temperature_c: "Temperature (°C)",
  oni_index: "ONI Index",
  state_identity: "State identity (fixed effects)",
  rainfall_anomaly: "Rainfall Anomaly (mm)",
  temp_anomaly: "Temp Anomaly (°C)",
  lagged_rainfall_mm: "Lagged Rainfall (t-1)",
  lagged_temperature_c: "Lagged Temp (t-1)",
  lagged_oni: "Lagged ONI (t-1)",
};
const CLIMATE_INPUTS = ["rainfall_mm", "avg_temperature_c", "oni_index"] as const;

interface Props {
  model: ModelName;
  importance: Record<string, number>;
  linearPermutation?: LinearClimatePermutation | null;
}

export default function FeatureImportanceChart({ model, importance, linearPermutation }: Props) {
  if (model === "linear_regression") {
    if (!linearPermutation) {
      return <p className="py-4 text-center text-xs text-slate-500">Held-out climate evaluation unavailable; no values are estimated for this chart.</p>;
    }
    const chartData = CLIMATE_INPUTS.map((key) => ({
      feature: FEATURE_LABELS[key],
      rmseChange: linearPermutation.rmse_change_cr[key],
    }));
    const maxMagnitude = Math.max(1, ...chartData.map((item) => Math.abs(item.rmseChange)));
    const axisLimit = Math.ceil(maxMagnitude * 1.1);

    return (
      <div>
        <h3 className="mb-2 text-sm font-semibold text-navy-900">
          {MODEL_LABELS[model]} — Held-Out Permutation Importance
        </h3>
        <p className="mb-3 text-xs text-slate-600">
          Change in test RMSE after shuffling each actual climate input (₹ crore). Positive = worse; negative = better.
        </p>
        <div className="h-56 w-full" role="img" aria-label={`Linear Regression held-out RMSE changes: ${chartData.map((item) => `${item.feature} ${item.rmseChange} crore`).join(", ")}`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" domain={[-axisLimit, axisLimit]} ticks={[-axisLimit, -axisLimit / 2, 0, axisLimit / 2, axisLimit]} tickFormatter={(value) => Number(value).toFixed(0)} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="feature" width={172} tick={{ fontSize: 11 }} />
              <ReferenceLine x={0} stroke="#64748b" />
              <Tooltip formatter={(value) => [`${Number(value).toFixed(2)} ₹ crore`, "Change in RMSE"]} />
              <Bar dataKey="rmseChange" radius={[0, 4, 4, 0]}>
                {chartData.map((item) => (
                  <Cell key={item.feature} fill={item.rmseChange < 0 ? "#d97706" : "#1e3a5f"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <dl className="mt-2 grid grid-cols-3 gap-1 text-center text-xs text-slate-700">
          {chartData.map((item) => (
            <div key={item.feature}>
              <dt className="text-slate-500">{item.feature}</dt>
              <dd className="font-semibold">{item.rmseChange >= 0 ? "+" : ""}{item.rmseChange.toFixed(2)} ₹ Cr</dd>
            </div>
          ))}
        </dl>
        <p className="mt-2 text-xs text-slate-500">
          {linearPermutation.test_years[0]}–{linearPermutation.test_years.at(-1)} test years · {linearPermutation.repeats} shuffles · baseline RMSE ₹{linearPermutation.baseline_rmse_cr.toLocaleString("en-IN")} Cr. State identity stays fixed. Unlike the tree charts, these are signed RMSE changes, not 0–1 scores or causal effects.
        </p>
      </div>
    );
  }

  if (!importance || Object.keys(importance).length === 0) {
    return <p className="text-xs text-slate-400 py-4 text-center">Feature importance not available</p>;
  }

  const chartData = Object.keys(importance).map((key) => ({
    feature: FEATURE_LABELS[key] || key.replace(/_/g, " "),
    importance: Number(importance[key]) || 0,
  }));

  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold text-navy-900">
        {MODEL_LABELS[model]} — Feature Importance
      </h3>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="feature" width={172} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => (typeof v === "number" ? v.toFixed(3) : String(v))} />
            <Bar dataKey="importance" fill="#1e3a5f" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
