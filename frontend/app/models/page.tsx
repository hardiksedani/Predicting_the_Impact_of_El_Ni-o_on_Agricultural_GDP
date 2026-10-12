"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Download, Info, Trophy } from "lucide-react";
import FeatureImportanceChart from "@/components/FeatureImportanceChart";
import LoadingSpinner from "@/components/LoadingSpinner";
import PageHeader from "@/components/PageHeader";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { ModelMetricsGroupedChart } from "@/components/ModelComparisonChart";
import { api, ApiError, ModelComparison } from "@/lib/api";
import { MODEL_DESCRIPTIONS, MODEL_LABELS, MODEL_NAMES } from "@/lib/constants";

export default function ModelsPage() {
  const [data, setData] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getModelComparison()
      .then(setData)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 404) {
          setError(
            "No official-data models yet. Run scripts/train_models.py manually after reviewing the new panel.",
          );
        } else {
          setError(e instanceof ApiError ? e.message : "Failed to load model metrics");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner label="Loading model comparison…" />;

  if (error || !data) {
    return (
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
        <PageHeader
          badge="ML Performance"
          title="Multi-Model Benchmark"
          description="Competitive benchmarking of 5 regression architectures evaluated on held-out chronological test years."
        />
        <Card>
          <CardContent className="py-12 text-center">
            <Brain className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 font-medium text-navy-900">{error ?? "No data"}</p>
            <Link href="/pipeline" className="mt-6 inline-block">
              <Button>View manual training steps</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const availableModels = MODEL_NAMES.filter((m) => data.models[m]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          badge="ML Performance"
          title="Multi-Model Benchmark"
          description={`Empirically selected best model: ${MODEL_LABELS[data.best_model]} (Lowest RMSE on held-out test data).`}
        />
        <div className="flex gap-2">
          <a
            href={api.getExportUrl("metrics", "csv")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            <Download className="h-4 w-4 text-slate-500" /> Export CSV
          </a>
          <a
            href={api.getExportUrl("metrics", "json")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            <Download className="h-4 w-4 text-slate-500" /> Export JSON
          </a>
        </div>
      </div>

      {/* Philosophy Banner */}
      <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
        <Info className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <p className="font-bold">Evaluation Methodology:</p>
          <p className="mt-0.5 text-blue-800 leading-relaxed">
            We evaluate multiple regression models on the same held-out years.
            The selected model has the lowest RMSE among these five on held-out financial years. The target is RBI/NSO crop GSVA, not GDP. MAE and RMSE are in ₹ crore; R² measures improvement against an overall-mean baseline, not percentage accuracy. Large differences in state size can make pooled R² high even when ₹ crore errors remain large. Compare with a simple state-mean baseline before claiming climate skill.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <Trophy className="h-5 w-5 text-amber-500" />
          <h3 className="text-lg font-semibold text-navy-900">Held-Out Test Set Metrics</h3>
        </CardHeader>
        <CardContent>
          <ModelMetricsGroupedChart data={data} />
          <div className="mt-6 overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50">
                <tr className="text-slate-500">
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">MAE (₹ crore)</th>
                  <th className="px-4 py-3">RMSE (₹ crore)</th>
                  <th className="px-4 py-3">R² Score</th>
                  <th className="px-4 py-3">MAPE (%)</th>
                  <th className="px-4 py-3">Training Time</th>
                </tr>
              </thead>
              <tbody>
                {availableModels.map((name) => {
                  const m = data.models[name];
                  if (!m) return null;
                  const isBest = data.best_model === name;
                  return (
                    <tr
                      key={name}
                      className={`border-t border-slate-100 ${
                        isBest ? "bg-emerald-50/80 font-medium" : ""
                      }`}
                    >
                      <td className="px-4 py-3 text-navy-900 flex items-center gap-2">
                        {MODEL_LABELS[name]}
                        {isBest && <Badge variant="success">Best Model</Badge>}
                      </td>
                      <td className="px-4 py-3">{m.mae.toFixed(2)}</td>
                      <td className="px-4 py-3 font-semibold">{m.rmse.toFixed(2)}</td>
                      <td className="px-4 py-3">{m.r2.toFixed(4)}</td>
                      <td className="px-4 py-3">{m.mape != null ? `${m.mape.toFixed(1)}%` : "—"}</td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {m.training_time_sec != null ? `${m.training_time_sec.toFixed(3)}s` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            Chronological Split: Training years {data.train_years.join(", ")} · Evaluation held-out test years:{" "}
            {data.test_years.join(", ")}
          </p>
          <div className="mt-5 grid gap-3 text-xs sm:grid-cols-3">
            <p className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-slate-700"><strong className="block text-navy-900">MAE (₹ crore)</strong>Average size of a prediction error, ignoring whether it was above or below the actual value.</p>
            <p className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-slate-700"><strong className="block text-navy-900">RMSE (₹ crore)</strong>Also measures error, but gives especially large misses more weight.</p>
            <p className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-slate-700"><strong className="block text-navy-900">R² (unitless)</strong>Improvement over predicting the overall test-set mean. It is not a percentage accuracy score.</p>
          </div>
        </CardContent>
      </Card>

      {/* Feature Importance Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {availableModels.map((name, i) => {
          const m = data.models[name];
          if (!m) return null;
          return (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <Card
                className={`h-full ${
                  data.best_model === name ? "ring-2 ring-emerald-400 ring-offset-2" : ""
                }`}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="h-5 w-5 text-indigo-500" />
                      <h3 className="font-bold text-navy-900 text-sm">{MODEL_LABELS[name]}</h3>
                    </div>
                    {data.best_model === name && <Badge variant="success">Best</Badge>}
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    {MODEL_DESCRIPTIONS[name]}
                  </p>
                </CardHeader>
                <CardContent>
                  <FeatureImportanceChart
                    model={name}
                    importance={m.feature_importance || {}}
                    linearPermutation={data.linear_permutation}
                  />
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
