"use client";

import { usePathname } from "next/navigation";

const titles: Record<string, string> = {
  "/": "Playground",
  "/history": "Run history (this browser)",
  "/styles": "Style bank",
  "/traces": "Evaluation traces",
  "/about": "About",
};

export function TopBar() {
  const pathname = usePathname();
  const base =
    pathname === "/"
      ? titles["/"]
      : Object.entries(titles).find(([p]) => p !== "/" && pathname.startsWith(p))?.[1] ??
        "KRR Retrieval";
  return (
    <header className="flex h-12 shrink-0 items-center border-b px-4 md:px-6">
      <h1 className="text-sm font-medium">{base}</h1>
    </header>
  );
}
