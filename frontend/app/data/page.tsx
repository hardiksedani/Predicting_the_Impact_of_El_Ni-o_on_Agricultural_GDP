"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Database, Download, Filter, Table2 } from "lucide-react";
import ErrorMessage from "@/components/ErrorMessage";
import LoadingSpinner from "@/components/LoadingSpinner";
import PageHeader from "@/components/PageHeader";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { api, ApiError, ClimateRow, StateSummary } from "@/lib/api";

export default function DataPage() {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [rows, setRows] = useState<ClimateRow[]>([]);
  const [filterState, setFilterState] = useState("");
  const [yearMin, setYearMin] = useState("");
  const [yearMax, setYearMax] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statesRes, dataRes] = await Promise.all([
        api.getStates(),
        api.getClimateData({
          state: filterState || undefined,
          year_min: yearMin ? Number(yearMin) : undefined,
          year_max: yearMax ? Number(yearMax) : undefined,
        }),
      ]);
      setStates(statesRes.states);
      setRows(dataRes.rows);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load dataset");
    } finally {
      setLoading(false);
    }
  }, [filterState, yearMin, yearMax]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          badge="Dataset Explorer"
          title="Panel Data Browser"
          description="Explore the new IMD/NOAA/RBI financial-year panel. Rows come from representative weather grid points and RBI/NSO crop GSVA, not the old sample dataset."
        />
        <div className="flex gap-2">
          <a
            href={api.getExportUrl("panel", "csv")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            <Download className="h-4 w-4 text-slate-500" /> Export CSV
          </a>
          <a
            href={api.getExportUrl("panel", "json")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            <Download className="h-4 w-4 text-slate-500" /> Export JSON
          </a>
        </div>
      </div>

      <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50 to-blue-50">
        <CardContent className="flex flex-wrap items-center gap-4 p-6">
          <div className="flex-1">
            <p className="font-semibold text-navy-900">New raw-data workflow</p>
            <p className="mt-1 text-sm text-slate-600">
              Review the prepared panel, then run the five-model training command
              yourself. The old automatic sample-data pipeline is disabled.
            </p>
          </div>
          <Link href="/pipeline">
            <Button>View manual steps</Button>
          </Link>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-indigo-500" />
          <h3 className="text-lg font-semibold text-navy-900">Filters</h3>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <select
              value={filterState}
              onChange={(e) => setFilterState(e.target.value)}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            >
              <option value="">All states</option>
              {states.map((s) => (
                <option key={s.state} value={s.state}>
                  {s.state}
                </option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Year min"
              value={yearMin}
              onChange={(e) => setYearMin(e.target.value)}
              className="w-32 rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <input
              type="number"
              placeholder="Year max"
              value={yearMax}
              onChange={(e) => setYearMax(e.target.value)}
              className="w-32 rounded-xl border border-slate-200 px-4 py-2.5 text-sm shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </CardContent>
      </Card>

      {error && <ErrorMessage message={error} />}

      <Card>
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Table2 className="h-5 w-5 text-indigo-500" />
            <h3 className="text-lg font-semibold text-navy-900">
              official_climate_gdp_data
            </h3>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
            {rows.length} rows
          </span>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner label="Loading dataset…" />
          ) : rows.length === 0 ? (
            <div className="py-16 text-center">
              <Database className="mx-auto h-12 w-12 text-slate-300" />
              <p className="mt-4 font-medium text-navy-900">No data in database</p>
              <p className="mt-2 text-sm text-slate-600">
                Prepare and sync the official raw-data panel from the project root.
              </p>
              <Link href="/pipeline" className="mt-6 inline-block">
                <Button>View preparation steps</Button>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-100">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50">
                  <tr className="text-slate-500">
                    <th className="px-4 py-3">State</th>
                    <th className="px-4 py-3">FY start year</th>
                    <th className="px-4 py-3">Rainfall (mm)</th>
                    <th className="px-4 py-3">Temp (°C)</th>
                    <th className="px-4 py-3">ONI</th>
                    <th className="px-4 py-3">Crop GSVA (₹ crore)</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr
                      key={`${row.state}-${row.year}`}
                      className="border-t border-slate-100 transition hover:bg-slate-50/80"
                    >
                      <td className="px-4 py-2.5 font-medium text-navy-900">
                        {row.state}
                      </td>
                      <td className="px-4 py-2.5">{row.year}</td>
                      <td className="px-4 py-2.5">{row.rainfall_mm.toFixed(1)}</td>
                      <td className="px-4 py-2.5">{row.avg_temperature_c.toFixed(1)}</td>
                      <td className="px-4 py-2.5">{row.oni_index.toFixed(2)}</td>
                      <td className="px-4 py-2.5">{row.agricultural_gdp_cr.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
