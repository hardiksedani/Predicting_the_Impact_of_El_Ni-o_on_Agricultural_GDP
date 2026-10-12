"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Brain,
  CloudRain,
  Globe2,
  Shield,
  TrendingDown,
  Zap,
} from "lucide-react";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import { api, DashboardSummary } from "@/lib/api";
import { MODEL_LABELS, MODEL_NAMES } from "@/lib/constants";

export default function HomePage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    api.getDashboardSummary().then(setSummary).catch(() => setSummary(null));
  }, []);

  const yearRange =
    summary?.year_min && summary?.year_max
      ? `${summary.year_min}–${summary.year_max}`
      : "—";

  const stats = [
    { label: "States Covered", value: summary?.states_count ?? "—", icon: Globe2 },
    { label: "FY Start Years", value: yearRange, icon: BarChart3 },
    { label: "ML Models", value: String(MODEL_NAMES.length), icon: Brain },
    {
      label: "Best Model",
      value: summary?.best_model ? MODEL_LABELS[summary.best_model] : "Not trained yet",
      icon: Zap,
    },
  ];

  const features = [
    {
      icon: CloudRain,
      title: "Official-data preparation",
      desc: "Combines your IMD grids, NOAA ONI, and RBI crop GSVA into a reviewed financial-year panel.",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: TrendingDown,
      title: "Crop GSVA Scenarios",
      desc: "Compare model estimates under hypothetical ONI, rainfall, and temperature conditions.",
      color: "from-indigo-500 to-purple-500",
    },
    {
      icon: Shield,
      title: "Policy Support",
      desc: "Analytical estimates for policymakers — not official government forecasts.",
      color: "from-violet-500 to-pink-500",
    },
  ];

  return (
    <div className="min-h-screen">
      <section className="relative overflow-hidden bg-gradient-to-br from-navy-900 via-indigo-950 to-navy-900 px-4 pb-24 pt-16 sm:px-6">
        <div className="hero-glow absolute inset-0" />
        <div className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl" />

        <div className="relative mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-center"
          >
            <Badge variant="info" className="mb-6 bg-blue-500/20 text-blue-200">
              K. J. Somaiya Institute of Technology · Dept. of AI &amp; Data Science
            </Badge>
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-6xl lg:text-7xl">
              El Niño &amp; Indian Crops
              <span className="mt-2 block gradient-text">State Crop GSVA Explorer</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300 leading-relaxed">
              Explore how ENSO and local weather relate to the value added by crop production in Indian states.
              Five models estimate crop GSVA—not total GDP—using IMD rainfall and temperature, NOAA ONI, and state identity.
              {summary?.best_model ? " Compare their hypothetical scenarios below." : " Predictions become available after you train them on the reviewed panel."}
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg">
                  <BarChart3 className="h-4 w-4" />
                  Explore Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/scenario">
                <Button variant="secondary" size="lg">
                  Scenario Lab
                </Button>
              </Link>
              <Link href="/search">
                <Button variant="secondary" size="lg">
                  AI Search Assistant
                </Button>
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="mt-16 grid grid-cols-2 gap-4 lg:grid-cols-4"
          >
            {stats.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="glass rounded-2xl p-5 text-center transition hover:bg-white/15"
              >
                <Icon className="mx-auto h-5 w-5 text-blue-300" />
                <p className="mt-3 text-2xl font-bold text-white">{value}</p>
                <p className="mt-1 text-xs text-slate-400">{label}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pt-16 sm:px-6">
        <Card className="border-blue-100 bg-blue-50/60">
          <CardContent className="space-y-4 p-6 sm:p-8">
            <h2 className="text-2xl font-bold text-navy-900">What does this project predict?</h2>
            <p className="max-w-4xl text-sm leading-relaxed text-slate-700">
              <strong>Crop GSVA</strong> (Gross State Value Added) is the value of crop production in one state
              after subtracting purchased production inputs. It is measured here in ₹ crore for an April–March
              financial year at constant 2011–12 prices. It is not farmer profit, a state&apos;s total GSDP, or India&apos;s GDP.
            </p>
            <div className="grid gap-3 text-sm sm:grid-cols-3">
              <div className="rounded-xl border border-blue-100 bg-white p-4"><strong className="text-navy-900">Crop GSVA</strong><p className="mt-1 text-slate-600">Crops within one state—the model&apos;s target.</p></div>
              <div className="rounded-xl border border-blue-100 bg-white p-4"><strong className="text-navy-900">GSDP</strong><p className="mt-1 text-slate-600">The whole state economy, across sectors and net product taxes.</p></div>
              <div className="rounded-xl border border-blue-100 bg-white p-4"><strong className="text-navy-900">GDP</strong><p className="mt-1 text-slate-600">The whole country&apos;s economy, across sectors and net product taxes.</p></div>
            </div>
            <Link href="/methodology" className="inline-flex text-sm font-semibold text-indigo-700 hover:underline">
              Read the definitions and data sources →
            </Link>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-navy-900">How It Works</h2>
          <p className="mt-2 text-slate-600">
            Prepare and review your official-data panel, then train the models yourself.
          </p>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {features.map(({ icon: Icon, title, desc, color }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="group h-full transition hover:-translate-y-1 hover:shadow-2xl">
                <CardContent className="p-6">
                  <div
                    className={`inline-flex rounded-xl bg-gradient-to-br ${color} p-3 shadow-lg`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-navy-900">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed">{desc}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-white px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <h2 className="text-center text-2xl font-bold text-navy-900">
            Five Models, One Crop-GSVA Target
          </h2>
          <p className="mt-2 text-center text-xs text-slate-500 max-w-xl mx-auto">
            The five models are compared on later held-out financial years. Lowest test RMSE selects the displayed model, but that score alone does not establish an El Niño effect.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {MODEL_NAMES.map((name) => (
              <div
                key={name}
                className={`rounded-2xl border p-5 text-center transition ${
                  summary?.best_model === name
                    ? "border-emerald-300 bg-emerald-50 shadow-lg shadow-emerald-100 ring-2 ring-emerald-400"
                    : "border-slate-200 bg-slate-50"
                }`}
              >
                <Brain className="mx-auto h-7 w-7 text-indigo-600" />
                <p className="mt-3 font-bold text-navy-900 text-sm">{MODEL_LABELS[name]}</p>
                {summary?.best_model === name ? (
                  <Badge variant="success" className="mt-2 text-xs">
                    Best Performer
                  </Badge>
                ) : (
                  <span className="mt-2 inline-block text-[11px] text-slate-400">Benchmark Model</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6">
        <Card className="overflow-hidden border-0 bg-gradient-to-r from-blue-600 to-indigo-700">
          <CardContent className="flex flex-col items-center p-10 text-center text-white sm:flex-row sm:text-left">
            <div className="flex-1">
              <h2 className="text-2xl font-bold">Ready to analyze?</h2>
              <p className="mt-2 text-blue-100">
                Review the new raw-data panel and run the five-model training command manually. The previous sample-data pipeline is disabled.
              </p>
            </div>
            <Link href="/pipeline" className="mt-6 sm:mt-0 sm:ml-6">
              <Button
                size="lg"
                className="bg-white text-indigo-700 hover:bg-blue-50 shadow-none"
              >
                View Manual Workflow
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
