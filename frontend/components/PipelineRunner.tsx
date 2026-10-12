import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";

/** Kept for existing imports; training is intentionally a local, manual action. */
export default function PipelineRunner() {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardContent className="space-y-3 p-6 text-sm text-amber-950">
        <h2 className="text-lg font-semibold">Manual official-data workflow</h2>
        <p>
          The former one-click pipeline is disabled. Prepare your IMD/NOAA/RBI panel,
          review its missing-value report, sync it, and run five-model training yourself.
        </p>
        <Link href="/pipeline" className="inline-block font-semibold underline underline-offset-2">
          View the PowerShell steps
        </Link>
      </CardContent>
    </Card>
  );
}
