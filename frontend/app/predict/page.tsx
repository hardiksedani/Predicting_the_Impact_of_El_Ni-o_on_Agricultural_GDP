"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { CloudRain, Droplets, Thermometer, Waves } from "lucide-react";
import Disclaimer from "@/components/Disclaimer";
import ErrorMessage from "@/components/ErrorMessage";
import LoadingSpinner from "@/components/LoadingSpinner";
import PageHeader from "@/components/PageHeader";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { api, ApiError, ModelComparison, PredictResponse, StateSummary } from "@/lib/api";
import { MODEL_LABELS, MODEL_NAMES, ONI_PRESETS } from "@/lib/constants";

function differenceLabel(pct: number): string {
  if (pct <= -20) return "much lower";
  if (pct <= -10) return "moderately lower";
  if (pct < 0) return "slightly lower";
  if (pct <= 5) return "near the historical mean";
  return "higher";
}

function buildInterpretation(result: PredictResponse): string {
  const avgDifferencePct =
    result.predictions.reduce((s, p) => s + p.predicted_impact_pct, 0) /
    result.predictions.length;
  return `The mean model estimate is ${differenceLabel(avgDifferencePct)} (${avgDifferencePct.toFixed(1)}%) relative to this state's historical crop-GSVA mean. This comparison does not identify a causal driver.`;
}

export default function PredictPage() {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [metrics, setMetrics] = useState<ModelComparison | null>(null);
  const [state, setState] = useState("");
  const [rainfall, setRainfall] = useState(700);
  const [temperature, setTemperature] = useState(30);
  const [oniIndex, setOniIndex] = useState(1.5);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getStates(),
      api.getModelComparison().catch(() => null),
    ])
      .then(([statesRes, metricsRes]) => {
        setStates(statesRes.states);
        setState(statesRes.states.find((s) => s.prediction_available)?.state ?? "");
        setMetrics(metricsRes);
      })
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Failed to load form data"),
      )
      .finally(() => setPageLoading(false));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.predict({
        state,
        rainfall,
        temperature,
        oni_index: oniIndex,
      });
      setResult(res);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Prediction failed. Review and sync the official panel, then train the five models manually.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (pageLoading) return <LoadingSpinner label="Loading prediction tool…" />;

  const availableCount = states.filter((s) => s.prediction_available).length;

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <PageHeader
        badge="Scenario Analysis"
        title="Predict Crop GSVA under Climate Scenarios"
        description="Enter financial-year rainfall, mean temperature, and ONI conditions to estimate state crop GSVA at constant 2011–12 prices. These are hypothetical model estimates, not GDP forecasts."
      />

      {states.length > 0 && (
        <p className="text-sm text-slate-600">
          Showing all {states.length} Indian states. Predictions are currently available for {availableCount};
          the others await your manual five-model training run.
        </p>
      )}

      {availableCount === 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="py-8 text-center">
            <p className="font-medium text-amber-900">No official-data predictions available yet</p>
            <p className="mt-1 text-sm text-amber-800">
              Prepare and sync the new raw-data panel, then train the five models manually.
            </p>
            <Link href="/pipeline" className="mt-4 inline-block">
              <Button>View manual steps</Button>
            </Link>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <h3 className="flex items-center gap-2 text-lg font-semibold text-navy-900">
            <CloudRain className="h-5 w-5 text-indigo-500" />
            Climate Scenario
          </h3>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-6">
            <div className="grid gap-5 sm:grid-cols-2">
              <label className="block">
                <span className="text-sm font-medium text-slate-700">State</span>
                <select
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  required
                >
                  <option value="" disabled>Select a state with trained data</option>
                  {states.map((s) => (
                    <option key={s.state} value={s.state} disabled={!s.prediction_available}>
                      {s.state}{s.prediction_available ? "" : " — data/training pending"}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block">
                <span className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
                  <Droplets className="h-4 w-4 text-blue-500" />
                  Rainfall (mm)
                </span>
                <input
                  type="number"
                  value={rainfall}
                  onChange={(e) => setRainfall(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  min={0}
                  step={0.1}
                  required
                />
              </label>

              <label className="block">
                <span className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
                  <Thermometer className="h-4 w-4 text-orange-500" />
                  Temperature (°C)
                </span>
                <input
                  type="number"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  step={0.1}
                  required
                />
              </label>

              <div className="block sm:col-span-2">
                <span className="flex items-center gap-1.5 text-sm font-medium text-slate-700">
                  <Waves className="h-4 w-4 text-cyan-500" />
                  ONI Index — El Niño strength
                </span>
                <input
                  type="range"
                  min={-2}
                  max={3}
                  step={0.1}
                  value={oniIndex}
                  onChange={(e) => setOniIndex(Number(e.target.value))}
                  className="mt-3 w-full accent-indigo-600"
                />
                <div className="mt-2 flex justify-between text-xs text-slate-500">
                  <span>La Niña (−2)</span>
                  <span className="rounded-full bg-indigo-100 px-3 py-1 font-bold text-indigo-700">
                    {oniIndex.toFixed(1)}
                  </span>
                  <span>Strong El Niño (+3)</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {ONI_PRESETS.map((p) => (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => setOniIndex(p.value)}
                      className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <Button type="submit" disabled={loading || !state} size="lg">
              {loading ? "Estimating…" : "Estimate Crop GSVA"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && <ErrorMessage message={error} />}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-navy-900">
                Results for {result.state}
              </h3>
              <p className="text-sm text-slate-600">
                Historical crop GSVA mean:{" "}
                <strong>₹{result.historical_avg_gdp_cr.toFixed(1)} crore</strong>
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {MODEL_NAMES.map((name) => {
                  const pred = result.predictions.find((p) => p.model === name);
                  if (!pred) return null;
                  const isNegative = pred.predicted_impact_pct < -10;
                  return (
                    <div
                      key={name}
                      className={`rounded-2xl border p-5 transition hover:shadow-lg ${
                        isNegative
                          ? "border-red-200 bg-gradient-to-br from-red-50 to-white"
                          : "border-slate-200 bg-gradient-to-br from-slate-50 to-white"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-500">
                          {MODEL_LABELS[name]}
                        </p>
                        {metrics?.best_model === name && (
                          <Badge variant="success">Best</Badge>
                        )}
                      </div>
                      <p className="mt-3 text-3xl font-bold text-navy-900">
                        ₹{pred.predicted_gdp_cr.toFixed(1)}
                        <span className="ml-1 text-base font-normal text-slate-500">
                          crore crop GSVA
                        </span>
                      </p>
                      <p
                        className={`mt-2 text-sm font-semibold ${
                          pred.predicted_impact_pct < 0
                            ? "text-red-700"
                            : "text-emerald-700"
                        }`}
                      >
                        {pred.predicted_impact_pct > 0 ? "+" : ""}
                        {pred.predicted_impact_pct.toFixed(1)}% vs historical mean
                      </p>
                    </div>
                  );
                })}
              </div>

              {result.ensemble_gdp_cr != null && (
                <p className="mt-6 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-900">
                  Mean crop-GSVA estimate across all models:{" "}
                  <strong>₹{result.ensemble_gdp_cr.toFixed(1)} crore</strong>
                </p>
              )}

              <p className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {buildInterpretation(result)}
              </p>

              <Disclaimer />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
