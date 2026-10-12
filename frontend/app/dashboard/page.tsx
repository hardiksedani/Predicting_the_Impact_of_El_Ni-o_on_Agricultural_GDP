"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  BarChart3,
  Brain,
  Calendar,
  ChevronRight,
  Database,
  Globe2,
  Sliders,
  TrendingUp,
  Zap,
} from "lucide-react";
import ErrorMessage from "@/components/ErrorMessage";
import GdpTrendChart from "@/components/GdpTrendChart";
import IndiaChoropleth from "@/components/IndiaChoropleth";
import LoadingSpinner from "@/components/LoadingSpinner";
import ModelComparisonChart from "@/components/ModelComparisonChart";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { api, ApiError, DashboardSummary, HistoryRow, ModelComparison, StateSummary } from "@/lib/api";
import { MODEL_LABELS } from "@/lib/constants";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [states, setStates] = useState<StateSummary[]>([]);
  const [selectedState, setSelectedState] = useState<string>("");
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [models, setModels] = useState<ModelComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modelsError, setModelsError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [sumRes, statesRes, modelsRes] = await Promise.all([
          api.getDashboardSummary().catch(() => null),
          api.getStates(),
          api.getModelComparison().catch((e) => {
            if (e instanceof ApiError && e.status === 404) {
              setModelsError("No official-data models yet. Train the five models manually after reviewing the new panel.");
              return null;
            }
            throw e;
          }),
        ]);
        if (sumRes) setSummary(sumRes);
        setStates(statesRes.states);
        setSelectedState(statesRes.states.find((s) => s.trend.length > 0)?.state ?? "");
        if (modelsRes) setModels(modelsRes);
      } catch (e) {
        setError(e instanceof ApiError ? e.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedState) return;
    api
      .getStateHistory(selectedState)
      .then((res) => setHistory(res.history))
      .catch(() => setHistory([]));
  }, [selectedState]);

  const impactByState = useMemo(() => {
    const result: Record<string, number> = {};
    for (const s of states) {
      if (s.trend.length === 0) continue;
      const values = s.trend.map((t) => t.agricultural_gdp_cr);
      const avg = values.reduce((a, b) => a + b, 0) / values.length;
      const latest = s.trend[s.trend.length - 1].agricultural_gdp_cr;
      result[s.state] = Math.round(((latest - avg) / avg) * 100 * 10) / 10;
    }
    return result;
  }, [states]);

  if (loading) return <LoadingSpinner label="Loading dashboard…" />;
  if (error) return <ErrorMessage message={error} />;

  const statesWithHistory = states.filter((s) => s.trend.length > 0).length;
  const emptyData = statesWithHistory === 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          badge="Analytics Dashboard"
          title="State Crop GSVA &amp; Climate Dashboard"
          description="Historical state crop GSVA, climate observations, and five-model benchmark. Crop GSVA is not total GDP."
        />
        <div className="flex gap-2">
          <Link href="/scenario">
            <Button size="md" variant="secondary">
              <Sliders className="h-4 w-4" /> Scenario Lab
            </Button>
          </Link>
          <Link href="/pipeline">
            <Button size="md">
              <Zap className="h-4 w-4" /> Manual Workflow
            </Button>
          </Link>
        </div>
      </div>

      {/* 6 KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <Globe2 className="mx-auto h-5 w-5 text-indigo-500 mb-1" />
            <p className="text-xl font-bold text-navy-900">{summary?.states_count ?? statesWithHistory}</p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">States Covered</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <Calendar className="mx-auto h-5 w-5 text-blue-500 mb-1" />
            <p className="text-xl font-bold text-navy-900">
              {summary?.year_min && summary?.year_max ? `${summary.year_min}–${summary.year_max}` : "—"}
            </p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">FY Start Years</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <Database className="mx-auto h-5 w-5 text-cyan-500 mb-1" />
            <p className="text-xl font-bold text-navy-900">{summary?.records_count ?? "—"}</p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">Total Records</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <Brain className="mx-auto h-5 w-5 text-purple-500 mb-1" />
            <p className="text-sm font-bold text-navy-900 truncate">
              {summary?.best_model ? MODEL_LABELS[summary.best_model] : "Pending"}
            </p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">Best Model</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <TrendingUp className="mx-auto h-5 w-5 text-emerald-500 mb-1" />
            <p className="text-xl font-bold text-emerald-600">
              {summary?.best_r2 != null ? summary.best_r2.toFixed(3) : "—"}
            </p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">Best R² Score</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-50 to-white">
          <CardContent className="p-4 text-center">
            <BarChart3 className="mx-auto h-5 w-5 text-amber-500 mb-1" />
            <p className="text-xl font-bold text-navy-900">
              {summary?.best_rmse != null ? `₹${summary.best_rmse.toFixed(1)}` : "—"}
            </p>
            <p className="text-[11px] text-slate-500 uppercase font-medium">Lowest RMSE (₹ crore)</p>
          </CardContent>
        </Card>
      </div>

      {emptyData ? (
        <Card>
          <CardContent className="py-16 text-center">
            <BarChart3 className="mx-auto h-12 w-12 text-slate-300" />
            <p className="mt-4 text-lg font-semibold text-navy-900">No data in database yet</p>
            <p className="mt-2 text-sm text-slate-600">
              Prepare and sync the new raw-data panel, then train the models manually.
            </p>
            <Link href="/pipeline" className="mt-6 inline-block">
              <Button>View manual steps</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-navy-900">
                    State Crop GSVA vs Each State&apos;s Historical Mean
                  </h3>
                  <p className="text-xs text-slate-500">
                    Color shows how the latest recorded crop GSVA differs from that state&apos;s own historical mean—not an El Niño impact estimate. Click a state to inspect it.
                  </p>
                </div>
                {selectedState && (
                  <Link
                    href={`/states/${encodeURIComponent(selectedState)}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:underline"
                  >
                    View {selectedState} Profile <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                )}
              </CardHeader>
              <CardContent>
                <IndiaChoropleth
                  impactByState={impactByState}
                  selectedState={selectedState}
                  onStateClick={setSelectedState}
                />
              </CardContent>
            </Card>
          </motion.div>

          <Card>
            <CardHeader className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-navy-900">
                Historical Crop GSVA &amp; ONI Index
              </h3>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              >
                {states.map((s) => (
                  <option key={s.state} value={s.state} disabled={s.trend.length === 0}>
                    {s.state}{s.trend.length > 0 ? "" : " — history pending"}
                  </option>
                ))}
              </select>
            </CardHeader>
            <CardContent>
              {history.length > 0 ? (
                <GdpTrendChart history={history} />
              ) : (
                <p className="py-8 text-center text-sm text-slate-500">
                  No history for selected state.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-navy-900">
                Crop GSVA Model Comparison (RMSE, ₹ crore)
              </h3>
            </CardHeader>
            <CardContent>
              {models ? (
                <ModelComparisonChart data={models} metric="rmse" />
              ) : (
                <ErrorMessage message={modelsError ?? "Model metrics unavailable."} />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
