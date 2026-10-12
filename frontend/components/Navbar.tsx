"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  Brain,
  CloudRain,
  Database,
  Home,
  Search,
  Sliders,
  Sparkles,
  Table2,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/predict", label: "Predict", icon: CloudRain },
  { href: "/scenario", label: "Scenario Lab", icon: Sliders },
  { href: "/models", label: "Models", icon: Brain },
  { href: "/search", label: "AI Search", icon: Search },
  { href: "/data", label: "Data Explorer", icon: Table2 },
  { href: "/methodology", label: "Methodology", icon: BookOpen },
  { href: "/pipeline", label: "Manual Workflow", icon: Database },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-navy-900/95 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="group flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30 transition group-hover:scale-105">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div className="hidden sm:block">
            <p className="text-[10px] font-medium uppercase tracking-widest text-blue-300/80">
              El Niño &amp; Crop Data
            </p>
            <p className="text-sm font-bold text-white leading-tight">
              Crop GSVA Explorer
            </p>
          </div>
        </Link>

        <nav className="flex items-center gap-1 overflow-x-auto">
          {links.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-xs font-medium transition-all sm:text-sm",
                  active
                    ? "bg-white/15 text-white shadow-inner"
                    : "text-slate-400 hover:bg-white/8 hover:text-white",
                )}
              >
                <Icon className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                <span className="hidden md:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
