import PageHeader from "@/components/PageHeader";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import {
  BarChart,
  Brain,
  CheckCircle2,
  Database,
  GraduationCap,
  Scale,
  ShieldCheck,
} from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <PageHeader
        badge="Academic Specification"
        title="Research Methodology & Data Dictionary"
        description="Detailed formulation of panel data construction, multi-model evaluation criteria, and economic target definitions."
      />

      {/* College PBL Identification Card */}
      <Card className="border-indigo-100 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="rounded-2xl bg-indigo-600 p-3 text-white shadow-md">
              <GraduationCap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                PBL Academic Project
              </p>
              <h2 className="mt-1 text-xl font-bold text-navy-900">
                Studying El Niño, Weather, and State Crop GSVA with Panel Data Machine Learning
              </h2>
              <p className="mt-1 text-sm text-slate-700">
                <strong>Institution:</strong> K. J. Somaiya Institute of Technology · Department of Artificial Intelligence and Data Science
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Methodology Pipeline Visual */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-bold text-navy-900">Analytical Pipeline Architecture</h3>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6 text-center">
            {[
              { step: "1. Data Acquisition", desc: "User-supplied IMD grids, NOAA ONI, RBI crop GSVA", icon: Database },
              { step: "2. Data Preprocessing", desc: "Missing-value and grid/date checks", icon: CheckCircle2 },
              { step: "3. Panel Construction", desc: "April–March state-year alignment", icon: Scale },
              { step: "4. Multi-Model ML", desc: "Train 5 regression models", icon: Brain },
              { step: "5. Empirical Selection", desc: "Lowest RMSE on held-out test years", icon: BarChart },
              { step: "6. Scenario Engine", desc: "Hypothetical policy simulation", icon: ShieldCheck },
            ].map((item, idx) => {
              const Icon = item.icon;
              return (
                <div key={idx} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <Icon className="mx-auto h-6 w-6 text-indigo-600 mb-2" />
                  <p className="text-xs font-bold text-navy-900">{item.step}</p>
                  <p className="mt-1 text-[11px] text-slate-500">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Target Variable Transparency */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-bold text-navy-900">Target Variable: Clarification &amp; Data Dictionary</h3>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-slate-700 leading-relaxed">
          <p>
            This project predicts <strong>crop Gross State Value Added (GSVA)</strong> for a state and financial year,
            not India&apos;s total GDP or a state&apos;s total GSDP. The selected RBI/NSO agriculture (crops) series
            excludes the separate forestry and fishing sectors.
          </p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { term: "GVA", meaning: "Gross Value Added: output minus purchased inputs used in production." },
              { term: "Crop GSVA", meaning: "Crop-sector value added within one state. This is our prediction target." },
              { term: "GSDP", meaning: "The whole state economy: value added across sectors plus net product taxes." },
              { term: "GDP", meaning: "The whole country economy: value added across sectors plus net product taxes." },
            ].map(({ term, meaning }) => (
              <div key={term} className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                <p className="font-semibold text-navy-900">{term}</p>
                <p className="mt-1 text-xs text-slate-700">{meaning}</p>
              </div>
            ))}
          </div>
          <p>
            For example, if crop output is worth ₹100 and purchased seeds, fertilizer, and other intermediate
            inputs cost ₹40, value added is ₹60. That ₹60 is <strong>not farmer profit</strong>; labour and other
            parts of production still have to be accounted for. “Gross” means depreciation has not been deducted.
          </p>
          <p>
            <strong>Constant 2011–12 prices</strong> aim to separate real production changes from price inflation.
            The older MoSPI economic PDFs use different base years and accounting definitions, so they are not
            silently joined to the selected RBI series. Climate downloads extend from 2001 to 2025, but the
            comparable selected target covers FY 2011–12 through 2024–25.
          </p>
          <p className="text-xs text-slate-600">
            Official definitions: <a className="font-semibold text-indigo-700 hover:underline" href="https://www.mospi.gov.in/uploads/announcements/announcements_1772117257791_84ae898f-7be2-4b7d-a135-565e1a809513_FAQ_GDP_26022026_1902.pdf" target="_blank" rel="noreferrer">MoSPI GDP and GVA FAQ</a>.
          </p>
          <div className="overflow-x-auto rounded-xl border border-slate-100">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3">Variable Name</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Units</th>
                  <th className="px-4 py-3">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="px-4 py-3 font-semibold text-navy-900">agricultural_gdp_cr</td>
                  <td className="px-4 py-3">Legacy API field name; the value is crop GSVA for an April–March financial year at constant 2011–12 prices, not GDP</td>
                  <td className="px-4 py-3">₹ crore</td>
                  <td className="px-4 py-3">RBI Table 30 / NSO</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-semibold text-navy-900">rainfall_mm</td>
                  <td className="px-4 py-3">Financial-year rainfall at a representative state grid point</td>
                  <td className="px-4 py-3">millimeters (mm)</td>
                  <td className="px-4 py-3">IMD 0.25° daily NetCDF grid</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-semibold text-navy-900">avg_temperature_c</td>
                  <td className="px-4 py-3">Financial-year mean of daily (Tmax + Tmin) / 2 at a representative point</td>
                  <td className="px-4 py-3">°Celsius</td>
                  <td className="px-4 py-3">IMD 1° daily GRD grids</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-semibold text-navy-900">oni_index</td>
                  <td className="px-4 py-3">Oceanic Niño Index (3-month SST Anomaly in Niño 3.4 Region)</td>
                  <td className="px-4 py-3">°Celsius</td>
                  <td className="px-4 py-3">NOAA Climate Prediction Center ASCII ONI</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 font-semibold text-navy-900">state identity</td>
                  <td className="px-4 py-3">One-hot state indicators calibrate different state output levels; not climate evidence</td>
                  <td className="px-4 py-3">0 or 1</td>
                  <td className="px-4 py-3">State label in the joined panel</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-500">
            * IMD rainfall, IMD temperature, NOAA ONI, and state identity are inputs; crop GSVA is the output.
            Weather uses the nearest IMD grid cell to one representative state point, not a statewide mean or station measurement.
            Cell centers can lie outside state boundaries, notably the coarse temperature cell near Goa.
          </p>
        </CardContent>
      </Card>

      {/* Multi-Model ML Philosophy */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-bold text-navy-900">Multi-Model Selection Philosophy</h3>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-slate-700 leading-relaxed">
          <p>
            Rather than presuming that one specific algorithm (such as XGBoost or Random Forest) is uniformly optimal,
            this platform implements a competitive multi-model benchmark across 5 architectures:
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="font-bold text-navy-900 text-sm">1. Linear Regression (OLS)</p>
              <p className="mt-1 text-xs text-slate-600">Serves as the classical econometric baseline and benchmark for explainability.</p>
            </div>
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="font-bold text-navy-900 text-sm">2. Random Forest Regressor</p>
              <p className="mt-1 text-xs text-slate-600">Non-linear bagging ensemble that reduces variance across noisy panel features.</p>
            </div>
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="font-bold text-navy-900 text-sm">3. Gradient Boosting Regressor</p>
              <p className="mt-1 text-xs text-slate-600">Sequential boosting algorithm that iteratively fits models to pseudo-residuals.</p>
            </div>
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50">
              <p className="font-bold text-navy-900 text-sm">4. XGBoost Regressor</p>
              <p className="mt-1 text-xs text-slate-600">Extreme gradient boosting with L1/L2 regularization to prevent overfitting on collinear climate signals.</p>
            </div>
            <div className="rounded-xl border border-slate-100 p-4 bg-slate-50 md:col-span-2">
              <p className="font-bold text-navy-900 text-sm">5. Extra Trees Regressor</p>
              <p className="mt-1 text-xs text-slate-600">Extremely randomized decision trees that optimize split thresholds across candidate features for lower bias.</p>
            </div>
          </div>
          <div className="rounded-xl bg-blue-50 p-4 border border-blue-100 text-xs text-blue-900">
            <strong>Chronological Evaluation Principle:</strong> Because panel data is time-dependent, random k-fold cross validation introduces temporal leakage.
            Models are trained on earlier financial years and evaluated on later held-out financial years. The actual year split is shown in the model report after your training run.
            The model exhibiting the minimum Root Mean Squared Error (RMSE) is selected among the five models.
            MAE and RMSE are measured in ₹ crore; a high pooled R² can still coexist with large errors because states differ greatly in economic size.
            Compare against a simple state-mean baseline before claiming the climate inputs add predictive value.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
