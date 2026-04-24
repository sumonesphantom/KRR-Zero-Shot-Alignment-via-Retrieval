import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";

export default function AboutPage() {
  return (
    <div className="mx-auto flex min-w-0 max-w-3xl flex-col gap-5">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">About</h2>
        <p className="text-sm text-muted-foreground">
          Zero-Shot Alignment via Retrieval — a KRR-based approach to
          preference-aligned generation.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">The problem</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 space-y-2">
          <p>
            Aligning an LLM's output to a new user's preferences by fine-tuning
            the base model does not scale. It is expensive, needs per-user data,
            and risks catastrophic forgetting.
          </p>
          <p>
            We cast the problem as knowledge retrieval: style modules are stored
            in a bank, indexed by their natural-language description. A user's
            preference is just a query; the retriever picks the right module and
            composes it onto a base model at inference time.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">How this UI works</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 space-y-2">
          <p>
            <Badge variant="secondary">1</Badge> You type a preference and a
            question. The retriever encodes the preference with
            sentence-transformers, scores every style card in the FAISS index,
            and returns the top-K matches.
          </p>
          <p>
            <Badge variant="secondary">2</Badge> The Knowledge LLM writes a
            plain factual draft — no style yet.
          </p>
          <p>
            <Badge variant="secondary">3</Badge> The Style LLM rewrites the
            draft using the retrieved style card (instruction + few-shot
            examples).
          </p>
          <p>
            <Badge variant="secondary">4</Badge> The Judge LLM scores the
            rewrite for style-match and content-preservation. A separate local
            cosine is computed between the draft and the styled output as an
            independent faithfulness check. If the verdict is not{" "}
            <code>accept</code>, the loop runs again (with the same style, or
            advancing to the next retrieval candidate, depending on the verdict
            action) up to <code>MAX_REVISIONS</code> times.
          </p>
          <p>
            <Badge variant="secondary">5</Badge> The UI streams every step over
            Server-Sent Events — you see retrieval results, the draft, each
            style attempt, and each judge verdict appear live.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Links</CardTitle>
        </CardHeader>
        <CardContent className="text-sm leading-6 space-y-1">
          <p>
            → <Link href="/" className="underline">Playground</Link>
          </p>
          <p>
            → <Link href="/styles" className="underline">Style bank</Link>
          </p>
          <p>
            → <Link href="/traces" className="underline">Past traces</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
