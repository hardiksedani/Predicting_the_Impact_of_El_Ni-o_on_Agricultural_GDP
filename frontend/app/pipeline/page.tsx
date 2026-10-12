import PageHeader from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/Card";

const steps = [
  {
    title: "1. Extract the RBI target",
    command: ".\\backend\\.venv\\Scripts\\python.exe scripts\\extract_economic_targets.py --overwrite",
    detail: "Keeps the 1999–2000 and 2004–05 publications separate. Training uses only the 2011–12-base RBI crop GSVA series.",
  },
  {
    title: "2. Build and review the official panel",
    command: ".\\backend\\.venv\\Scripts\\python.exe scripts\\prepare_official_panel.py --overwrite",
    detail: "Combines your IMD rainfall and temperature grids, NOAA ONI, and RBI targets by April–March financial year. Review official_panel_report.json before continuing.",
  },
  {
    title: "3. Sync the website history",
    command: ".\\backend\\.venv\\Scripts\\python.exe scripts\\sync_official_panel.py",
    detail: "Writes the validated panel to a separate official collection. The old sample records are not read by the website.",
  },
  {
    title: "4. Train the five models yourself",
    command: ".\\backend\\.venv\\Scripts\\python.exe scripts\\train_models.py",
    detail: "Runs a chronological test split and records state coverage. Run it yourself only when you intend to create a new active five-model run.",
  },
];

export default function PipelinePage() {
  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6">
      <PageHeader
        badge="New raw-data workflow"
        title="Prepare and Train from Your Files"
        description="The old automatic Open-Meteo/sample-target pipeline is disabled. These commands use your local IMD, NOAA, and RBI files."
      />
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="p-6 text-sm text-amber-950">
          Run the commands in a VS Code PowerShell terminal from the project root.
          The climate values use nearest IMD grid-cell proxies to one representative point per state, not state-wide averages. A center may lie outside the state, notably Goa&apos;s coarse temperature cell.
          The target is RBI/NSO crop GSVA at constant 2011–12 prices, not total GDP.
        </CardContent>
      </Card>
      <div className="grid gap-4">
        {steps.map((step) => (
          <Card key={step.title}>
            <CardContent className="space-y-3 p-6">
              <h2 className="font-semibold text-navy-900">{step.title}</h2>
              <p className="text-sm text-slate-600">{step.detail}</p>
              <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-50"><code>{step.command}</code></pre>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
