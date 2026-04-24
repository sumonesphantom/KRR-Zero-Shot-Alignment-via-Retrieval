"use client";

import Link from "next/link";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Separator } from "../ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "../ui/sheet";
import type { StyleCard } from "../../lib/api/types";

export function StyleDetailDrawer({
  card,
  open,
  onOpenChange,
}: {
  card: StyleCard | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!card) return null;

  const preferenceSeed = card.tags.slice(0, 3).join(", ");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{card.id}</SheetTitle>
          <SheetDescription>
            <div className="flex flex-wrap gap-1 mt-1">
              {card.tags.map((t) => (
                <Badge key={t} variant="secondary" className="text-[10px]">
                  {t}
                </Badge>
              ))}
            </div>
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 flex flex-col gap-4">
          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Instruction
            </h3>
            <p className="text-sm leading-6">{card.instruction}</p>
          </div>

          {card.examples.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                  Few-shot examples
                </h3>
                <Accordion type="single" collapsible>
                  {card.examples.map((ex, i) => (
                    <AccordionItem key={i} value={`ex-${i}`}>
                      <AccordionTrigger className="text-sm">
                        {ex.prompt}
                      </AccordionTrigger>
                      <AccordionContent>
                        <p className="whitespace-pre-wrap text-sm leading-6 rounded-md bg-muted/40 p-3">
                          {ex.answer}
                        </p>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </>
          )}

          {card.adapterPath && (
            <>
              <Separator />
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                  Adapter path
                </h3>
                <code className="text-xs font-mono bg-muted/60 px-2 py-1 rounded">
                  {card.adapterPath}
                </code>
              </div>
            </>
          )}

          <Separator />
          <div>
            <Button asChild size="sm">
              <Link
                href={{
                  pathname: "/",
                  query: { preference: preferenceSeed },
                }}
                onClick={() => onOpenChange(false)}
              >
                Try in Playground
              </Link>
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
