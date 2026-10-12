"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Droplets,
  Layers,
  Sliders,
  Sparkles,
  Thermometer,
  TrendingDown,
  TrendingUp,
  Waves,
} from "lucide-react";
import Disclaimer from "@/components/Disclaimer";
import ErrorMessage from "@/components/ErrorMessage";
import LoadingSpinner from "@/components/LoadingSpinner";
import PageHeader from "@/components/PageHeader";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { api, ApiError, ScenarioResponse, StateSummary } from "@/lib/api";
import { ONI_PRESETS } from "@/lib/constants";

export default function ScenarioPage() {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [selectedState, setSelectedState] = useState("");
  const [rainfall, setRainfall] = useState(720);
  const [temperature, setTemperature] = useState(29.5);
  const [oniIndex, setOniIndex] = useState(1.5);
  const [activePreset, setActivePreset] = useState("Moderate El Niño");
  const [result, setResult] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getStates()
      .then((statesRes) => {
        setStates(statesRes.states);
        setSelectedState(statesRes.states.find((s) => s.prediction_available)?.state ?? "");
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load state metadata"))
      .finally(() => setPageLoading(false));
  }, []);

  async function handleSimulate(stateToUse = selectedState, rain = rainfall, temp = temperature, oni = oniIndex, preset = activePreset) {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runScenario({
        state: stateToUse,
        rainfall: rain,
        temperature: temp,
        oni_index: oni,
        preset_name: preset,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Simulation failed. Review and sync the official panel, then train the five models manually.");
    } finally {
      setLoading(false);
    }
  }

  function applyPreset(presetLabel: string, presetVal: number) {
    setActivePreset(presetLabel);
    setOniIndex(presetVal);

    // Contextual rainfall/temp adjustments based on preset severity
    let adjustedRain = 750;
    let adjustedTemp = 28.5;
    if (presetLabel.includes("Strong")) {
      adjustedRain = 520;
      adjustedTemp = 31.0;
    } else if (presetLabel.includes("Moderate")) {
      adjustedRain = 640;
      adjustedTemp = 29.8;
    } else if (presetLabel.includes("Weak")) {
      adjustedRain = 720;
      adjustedTemp = 28.8;
    } else if (presetLabel.includes("Neutral")) {
      adjustedRain = 850;
      adjustedTemp = 28.0;
    } else if (presetLabel.includes("La Niña")) {
      adjustedRain = 1020;
      adjustedTemp = 27.2;
    }

    setRainfall(adjustedRain);
    setTemperature(adjustedTemp);
    if (selectedState) {
      handleSimulate(selectedState, adjustedRain, adjustedTemp, presetVal, presetLabel);
    }
  }

  // Trigger initial simulation once states load
  useEffect(() => {
    if (selectedState && !result) {
      handleSimulate(selectedState, rainfall, temperature, oniIndex, activePreset);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedState]);

  if (pageLoading) return <LoadingSpinner label="Loading Scenario Laboratory…" />;

  const availableCount = states.filter((s) => s.prediction_available).length;

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <PageHeader
        badge="Hypothetical Model Scenario"
        title="El Niño Scenario Laboratory"
        description="Explore hypothetical combinations of ONI, rainfall, and temperature to estimate crop GSVA—not total GDP. Preset weather values are illustrative, not ENSO-caused forecasts."
      />
      <p className="text-sm text-slate-600">
        All {states.length} Indian states are listed. Scenario predictions are available for {availableCount};
        the others need a validated training panel and retraining.
      </p>

      {/* Preset Selector */}
      <Card className="border-indigo-100 bg-gradient-to-r from-navy-900 via-indigo-950 to-navy-900 text-white">
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-300">
            <Sparkles className="h-4 w-4" /> Quick Presets
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {ONI_PRESETS.map((p) => {
              const active = activePreset === p.label;
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => applyPreset(p.label, p.value)}
                  className={`rounded-xl border p-4 text-left transition ${
                    active
                      ? "border-blue-400 bg-blue-500/20 shadow-lg shadow-blue-500/20"
                      : "border-white/10 bg-white/5 hover:bg-white/10 text-slate-300"
                  }`}
                >
                  <p className="font-bold text-white text-sm">{p.label}</p>
                  <p className="mt-1 text-xs text-blue-200">ONI: {p.value > 0 ? `+${p.value}` : p.value}°C</p>
                  <p className="mt-2 text-[11px] text-slate-400 leading-tight">{p.desc}</p>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Input Sliders & Selectors */}
      <Card>
        <CardHeader className="flex items-center gap-2">
          <Sliders className="h-5 w-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-navy-900">Custom Meteorological Parameters</h3>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Target State</label>
              <select
                value={selectedState}
                onChange={(e) => {
                  setSelectedState(e.target.value);
                  handleSimulate(e.target.value, rainfall, temperature, oniIndex, activePreset);
                }}
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              >
                <option value="" disabled>Select a state with trained data</option>
                {states.map((s) => (
                  <option key={s.state} value={s.state} disabled={!s.prediction_available}>
                    {s.state}{s.prediction_available ? "" : " — data/training pending"}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                <span className="flex items-center gap-1">
                  <Droplets className="h-4 w-4 text-blue-500" /> Rainfall (mm)
                </span>
                <span className="font-bold text-navy-900">{rainfall} mm</span>
              </div>
              <input
                type="range"
                min={200}
                max={2500}
                step={10}
                value={rainfall}
                onChange={(e) => setRainfall(Number(e.target.value))}
                className="mt-3 w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                <span className="flex items-center gap-1">
                  <Thermometer className="h-4 w-4 text-orange-500" /> Temp (°C)
                </span>
                <span className="font-bold text-navy-900">{temperature}°C</span>
              </div>
              <input
                type="range"
                min={15}
                max={42}
                step={0.2}
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="mt-3 w-full accent-orange-500"
              />
            </div>

            <div>
              <div className="flex items-center justify-between text-sm font-medium text-slate-700">
                <span className="flex items-center gap-1">
                  <Waves className="h-4 w-4 text-cyan-500" /> ONI Index
                </span>
                <span className="font-bold text-navy-900">{oniIndex > 0 ? `+${oniIndex}` : oniIndex}</span>
              </div>
              <input
                type="range"
                min={-2.0}
                max={3.0}
                step={0.1}
                value={oniIndex}
                onChange={(e) => setOniIndex(Number(e.target.value))}
                className="mt-3 w-full accent-indigo-600"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <Button
              onClick={() => handleSimulate(selectedState, rainfall, temperature, oniIndex, activePreset)}
              disabled={loading || !selectedState}
              size="md"
            >
              {loading ? "Simulating Scenario…" : "Run Simulation"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && <ErrorMessage message={error} />}

      {/* Simulation Results */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          {/* Key KPI Banner */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium text-slate-500 uppercase">Historical Crop GSVA Mean</p>
                <p className="mt-2 text-2xl font-bold text-navy-900">
                  ₹{result.historical_avg_gdp_cr.toLocaleString()} <span className="text-xs text-slate-500 font-normal">Cr</span>
                </p>
                <p className="mt-1 text-xs text-slate-500">RBI/NSO crops, constant 2011–12 prices</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-slate-500 uppercase">Selected Model Crop GSVA</p>
                  <Badge variant="success">Lowest RMSE</Badge>
                </div>
                <p className="mt-2 text-2xl font-bold text-navy-900">
                  ₹{result.best_model_result.predicted_gdp_cr.toLocaleString()} <span className="text-xs text-slate-500 font-normal">Cr</span>
                </p>
                <p className="mt-1 text-xs text-indigo-600 font-medium">
                  {result.best_model_result.model_name_display}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium text-slate-500 uppercase">Difference vs Historical Mean</p>
                <p
                  className={`mt-2 text-2xl font-bold flex items-center gap-1 ${
                    result.best_model_result.predicted_impact_pct < 0 ? "text-red-600" : "text-emerald-600"
                  }`}
                >
                  {result.best_model_result.predicted_impact_pct < 0 ? (
                    <TrendingDown className="h-6 w-6" />
                  ) : (
                    <TrendingUp className="h-6 w-6" />
                  )}
                  {result.best_model_result.predicted_impact_pct > 0 ? "+" : ""}
                  {result.best_model_result.predicted_impact_pct.toFixed(1)}%
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  {result.best_model_result.absolute_change_cr > 0 ? "+" : ""}
                  ₹{result.best_model_result.absolute_change_cr.toLocaleString()} crore model difference
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-medium text-slate-500 uppercase">Mean Crop GSVA Estimate</p>
                <p className="mt-2 text-2xl font-bold text-navy-900">
                  ₹{result.ensemble_gdp_cr?.toLocaleString()} <span className="text-xs text-slate-500 font-normal">Cr</span>
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Mean estimate from all 5 regression models
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Model Comparison Grid */}
          <Card>
            <CardHeader className="flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-500" />
              <h3 className="text-lg font-semibold text-navy-900">Multi-Model Crop GSVA Estimates</h3>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                {result.predictions.map((p) => {
                  const isBest = p.model === result.best_model_result.model;
                  const isNeg = p.predicted_impact_pct < 0;
                  return (
                    <div
                      key={p.model}
                      className={`rounded-xl border p-4 transition ${
                        isBest
                          ? "border-emerald-300 bg-emerald-50/50 shadow-sm ring-1 ring-emerald-400"
                          : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-bold text-slate-600 truncate">{p.model_name_display}</p>
                        {isBest && <Badge variant="success">Best</Badge>}
                      </div>
                      <p className="mt-3 text-xl font-bold text-navy-900">
                        ₹{p.predicted_gdp_cr.toLocaleString()} <span className="text-xs font-normal text-slate-500">Cr</span>
                      </p>
                      <p
                        className={`mt-1 text-xs font-semibold ${
                          isNeg ? "text-red-600" : "text-emerald-600"
                        }`}
                      >
                        {p.predicted_impact_pct > 0 ? "+" : ""}
                        {p.predicted_impact_pct.toFixed(1)}% vs historical mean
                      </p>
                      <p className="mt-1 text-[11px] text-slate-400">
                        Diff: {p.absolute_change_cr > 0 ? "+" : ""}₹{p.absolute_change_cr.toLocaleString()} Cr
                      </p>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 rounded-xl bg-slate-50 p-4 border border-slate-100">
                <p className="text-sm font-semibold text-navy-900">Model interpretation—not causal attribution:</p>
                <p className="mt-1 text-sm text-slate-600 leading-relaxed">{result.interpretation}</p>
              </div>

              <div className="mt-4">
                <Disclaimer />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
