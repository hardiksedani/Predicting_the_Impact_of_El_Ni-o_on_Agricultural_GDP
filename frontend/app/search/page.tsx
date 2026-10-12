"use client";

import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  Brain,
  Database,
  ExternalLink,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import Disclaimer from "@/components/Disclaimer";
import ErrorMessage from "@/components/ErrorMessage";
import LoadingSpinner from "@/components/LoadingSpinner";
import PageHeader from "@/components/PageHeader";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { api, ApiError, SearchResponse } from "@/lib/api";

const EXAMPLE_QUERIES = [
  "What is El Niño and how does NOAA define the Oceanic Niño Index (ONI)?",
  "How does El Niño affect the Indian Southwest monsoon and agriculture?",
  "What is the estimated crop GSVA for Maharashtra under a moderate El Niño scenario?",
  "What happens to Punjab under a strong El Niño scenario?",
  "Which states have the highest historical crop GSVA?",
];

const INTENT_BADGES = {
  factual: { label: "Climate Science Fact", variant: "info" as const, icon: BookOpen },
  historical: { label: "Database Query", variant: "default" as const, icon: Database },
  prediction: { label: "ML Model Prediction", variant: "success" as const, icon: Brain },
  scenario: { label: "Hypothetical Scenario", variant: "warning" as const, icon: Zap },
  mixed: { label: "Multi-Source Insight", variant: "info" as const, icon: Sparkles },
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function executeSearch(q: string) {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setQuery(q);
    try {
      const res = await api.search(q);
      setResult(res);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Search query failed. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    executeSearch(query);
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <PageHeader
        badge="Two-Tier Intelligence Assistant"
        title="El Niño & Agriculture Search Assistant"
        description="Ask about ENSO, query the new official-data panel, or request a model scenario after manual training. Verify answers against the cited sources."
      />

      {/* Search Input Box */}
      <Card className="border-indigo-100 shadow-md">
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-3.5 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Ask about El Niño, Indian monsoon, state-wise predictions, or historical trends..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded-xl border border-slate-200 py-3 pl-12 pr-4 text-sm shadow-inner focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
              />
            </div>
            <Button type="submit" disabled={loading || !query.trim()} size="lg">
              {loading ? "Searching…" : "Search"}
            </Button>
          </form>

          {/* Quick Examples */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Example queries:</span>
            {EXAMPLE_QUERIES.map((eq) => (
              <button
                key={eq}
                type="button"
                onClick={() => executeSearch(eq)}
                className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-900 text-left"
              >
                {eq}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {error && <ErrorMessage message={error} />}

      {loading && <LoadingSpinner label="Classifying intent and retrieving grounded answer…" />}

      {/* Search Result Display */}
      {result && !loading && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <Card className="overflow-hidden border-slate-200">
            <CardHeader className="bg-gradient-to-r from-slate-50 to-white flex flex-row items-center justify-between border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Search className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-navy-900">Query Analysis &amp; Answer</h3>
              </div>
              {result.intent && INTENT_BADGES[result.intent] && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">Query Classification:</span>
                  <Badge variant={INTENT_BADGES[result.intent].variant}>
                    {INTENT_BADGES[result.intent].label}
                  </Badge>
                </div>
              )}
            </CardHeader>

            <CardContent className="p-6 space-y-6">
              <div className="rounded-xl bg-slate-50 p-5 border border-slate-100">
                <p className="text-xs font-semibold uppercase text-slate-400">User Query</p>
                <p className="mt-1 font-medium text-navy-900 text-base">{result.query}</p>
              </div>

              {/* Synthesized Grounded Response */}
              <div className="prose prose-slate max-w-none text-slate-800 leading-relaxed whitespace-pre-line">
                {result.answer}
              </div>

              {/* Verified Sources & Citations */}
              {result.citations && result.citations.length > 0 && (
                <div className="mt-6 border-t border-slate-100 pt-6">
                  <h4 className="flex items-center gap-2 text-sm font-bold text-navy-900 mb-3">
                    <BookOpen className="h-4 w-4 text-indigo-500" />
                    Verified Citations &amp; Trusted Sources
                  </h4>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {result.citations.map((c, i) => (
                      <div key={i} className="rounded-xl border border-slate-100 bg-slate-50 p-4 transition hover:bg-white hover:shadow-sm">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-bold text-indigo-700">{c.source}</p>
                          {c.url && (
                            <a
                              href={c.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-400 hover:text-indigo-600"
                            >
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          )}
                        </div>
                        <p className="mt-1 font-semibold text-navy-900 text-xs">{c.title}</p>
                        <p className="mt-1 text-[11px] text-slate-600 leading-normal">{c.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="border-t border-slate-100 pt-4">
                <Disclaimer />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
