"use client";

import { useState } from "react";

import type { StyleCard } from "@/lib/api/types";
import { StyleCardTile } from "@/components/styles/StyleCardTile";
import { StyleDetailDrawer } from "@/components/styles/StyleDetailDrawer";

export function StyleGrid({ styles }: { styles: StyleCard[] }) {
  const [active, setActive] = useState<StyleCard | null>(null);

  return (
    <>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {styles.map((s) => (
          <StyleCardTile key={s.id} card={s} onOpen={() => setActive(s)} />
        ))}
      </div>
      <StyleDetailDrawer
        card={active}
        open={active !== null}
        onOpenChange={(open) => !open && setActive(null)}
      />
    </>
  );
}
