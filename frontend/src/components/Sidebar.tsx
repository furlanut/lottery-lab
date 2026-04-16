"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Dice1, Home, Calendar, Timer, FlaskConical, TrendingUp } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/lotto", label: "Lotto", icon: Dice1 },
  { href: "/vincicasa", label: "VinciCasa", icon: Home },
  { href: "/calendario", label: "Calendario", icon: Calendar },
  { href: "/diecielotto", label: "10eLotto", icon: Timer },
  { href: "/diecielotto-lab", label: "10eL Lab", icon: FlaskConical },
  { href: "/paper-trading", label: "P&L", icon: TrendingUp },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex fixed top-0 left-0 z-40 h-full w-60 flex-col">
        {/* Sidebar background */}
        <div className="absolute inset-0 bg-[rgba(5,5,16,0.95)] border-r border-[rgba(255,255,255,0.06)]" />

        <div className="relative flex flex-col h-full">
          {/* Logo */}
          <div className="px-5 py-6 mb-2">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-lotto-blue to-lotto-purple flex items-center justify-center flex-shrink-0 shadow-lg shadow-lotto-blue/30">
                <span className="text-white font-black text-sm">L</span>
              </div>
              <div>
                <p className="text-white font-bold text-sm leading-none">Lottery Lab</p>
                <p className="text-[10px] text-lotto-muted mt-0.5 leading-none">Sistema predittivo</p>
              </div>
            </Link>
          </div>

          {/* Divider */}
          <div className="mx-5 h-px bg-[rgba(255,255,255,0.06)] mb-4" />

          {/* Nav items */}
          <nav className="flex-1 px-3 space-y-0.5">
            {navItems.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                    transition-all duration-150 group
                    ${
                      isActive
                        ? "bg-gradient-to-r from-lotto-blue/15 to-lotto-purple/5 text-white"
                        : "text-lotto-muted hover:text-lotto-text hover:bg-[rgba(255,255,255,0.04)]"
                    }
                  `}
                >
                  {isActive && (
                    <span className="nav-active-indicator" />
                  )}
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition-colors ${
                      isActive ? "text-lotto-blue" : "text-lotto-muted group-hover:text-lotto-text"
                    }`}
                  />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-5 py-4 mt-auto">
            <div className="h-px bg-[rgba(255,255,255,0.06)] mb-3" />
            <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.06)]">
              <span className="w-1.5 h-1.5 rounded-full bg-lotto-green dot-pulse" />
              <span className="text-[10px] text-lotto-muted font-medium">v1.0.0</span>
            </span>
          </div>
        </div>
      </aside>

      {/* Mobile bottom navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around px-2 py-2 bg-[rgba(5,5,16,0.97)] border-t border-[rgba(255,255,255,0.08)] backdrop-blur-xl">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-all ${
                isActive
                  ? "text-lotto-blue"
                  : "text-lotto-muted"
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[9px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
