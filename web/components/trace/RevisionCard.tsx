"use client";

import { ChevronDown } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import { Badge } from "../ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { ActionBadge } from "./ActionBadge";
import { CosineBadge, StyleScoreBadge } from "./VerdictBadge";
import type { RevisionStep } from "../../lib/api/types";

export function RevisionCard({
  step,
  awaitingVerdict,
  awaitingStyled,
  streaming,
}: {
  step: RevisionStep;
  awaitingVerdict: boolean;
  awaitingStyled?: boolean;
  streaming?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <span className="text-muted-foreground">Attempt {step.attempt} · </span>
            <Badge variant="outline">{step.styleId}</Badge>
          </CardTitle>
          <div className="flex items-center gap-2 flex-wrap">
            {streaming ? (
              <Badge variant="secondary" className="animate-pulse">streaming…</Badge>
            ) : awaitingVerdict ? (
              <Badge variant="secondary" className="animate-pulse">judging…</Badge>
            ) : (
              <>
                <StyleScoreBadge score={step.verdict.styleScore} />
                <CosineBadge cosine={step.verdict.contentCosine} />
                <ActionBadge action={step.verdict.action} />
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="mb-1 text-xs font-medium text-muted-foreground">
            Styled output
          </div>
          {awaitingStyled && !step.styled ? (
            <div className="space-y-2">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-[92%]" />
              <Skeleton className="h-3 w-[75%]" />
            </div>
          ) : (
            <p className="whitespace-pre-wrap text-sm leading-6 rounded-md bg-muted/40 p-3">
              {step.styled || (
                <span className="italic text-muted-foreground">(empty)</span>
              )}
              {streaming && (
                <span
                  className="inline-block w-[0.4em] h-[1em] ml-[1px] bg-primary align-[-0.1em] animate-pulse"
                  aria-hidden="true"
                />
              )}
            </p>
          )}
        </div>

        {!awaitingVerdict && step.verdict.rationale && (
          <div className="text-xs text-muted-foreground italic">
            “{step.verdict.rationale}”
          </div>
        )}

        {!awaitingVerdict && step.verdict.raw && (
          <Accordion type="single" collapsible>
            <AccordionItem value="raw" className="border-0">
              <AccordionTrigger className="py-1 text-xs text-muted-foreground hover:no-underline">
                Raw judge output
              </AccordionTrigger>
              <AccordionContent>
                <pre className="whitespace-pre-wrap rounded-md bg-muted/60 p-2 text-xs font-mono">
                  {step.verdict.raw}
                </pre>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
      </CardContent>
    </Card>
  );
}
