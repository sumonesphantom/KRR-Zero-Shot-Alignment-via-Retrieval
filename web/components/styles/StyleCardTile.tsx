"use client";

import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { truncate } from "../../lib/format";
import type { StyleCard as TStyleCard } from "../../lib/api/types";

export function StyleCardTile({
  card,
  onOpen,
}: {
  card: TStyleCard;
  onOpen: () => void;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">{card.id}</CardTitle>
        <div className="flex flex-wrap gap-1 mt-1">
          {card.tags.slice(0, 4).map((t) => (
            <Badge key={t} variant="secondary" className="text-[10px]">
              {t}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground leading-6">
          {truncate(card.instruction, 180)}
        </p>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm" onClick={onOpen}>
          View details
        </Button>
      </CardFooter>
    </Card>
  );
}
