"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Clock,
  History,
  Layers,
  PlayCircle,
  Info,
} from "lucide-react";

import { cn } from "../../lib/utils";
import { ThemeToggle } from "./ThemeToggle";
import { HealthDot } from "./HealthDot";

const items = [
  { href: "/", label: "Playground", icon: PlayCircle },
  { href: "/history", label: "History", icon: Clock },
  { href: "/styles", label: "Styles", icon: Layers },
  { href: "/traces", label: "Eval traces", icon: History },
  { href: "/about", label: "About", icon: Info },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="px-4 py-5 border-b">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <span className="font-semibold">KRR Retrieval</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Zero-shot style alignment
        </p>
      </div>

      <nav className="flex-1 px-2 py-3">
        <ul className="flex flex-col gap-1">
          {items.map((it) => {
            const active =
              it.href === "/" ? pathname === "/" : pathname.startsWith(it.href);
            const Icon = it.icon;
            return (
              <li key={it.href}>
                <Link
                  href={it.href}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                      : "text-sidebar-foreground/80 hover:bg-sidebar-accent/50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {it.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t px-3 py-3 flex items-center justify-between">
        <HealthDot />
        <ThemeToggle />
      </div>
    </aside>
  );
}
