import { HealthBanner } from "@/components/playground/HealthBanner";
import { JudgePlayground } from "@/components/playground/JudgePlayground";

export default function PlaygroundPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-7xl flex-col gap-4">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Playground</h2>
        <p className="text-sm text-muted-foreground">
          Describe your preference, ask a question, watch retrieval → draft →
          style → judge stream live.
        </p>
      </div>
      <HealthBanner />
      <JudgePlayground />
    </div>
  );
}
