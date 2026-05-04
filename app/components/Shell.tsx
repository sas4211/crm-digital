"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard, Ticket, Users, AlertTriangle, BarChart2,
  Settings, Bell, Search, ChevronDown,
  Globe, Menu, X, Command
} from "lucide-react";
import { cn } from "@/app/lib/utils";

/* ─── Nav config ─────────────────────────────────────────────────────────────── */
const NAV = [
  { label: "Dashboard",   Icon: LayoutDashboard, href: "/"             },
  { label: "Tickets",     Icon: Ticket,          href: "/tickets"      },
  { label: "Customers",   Icon: Users,           href: "/customers"    },
  { label: "Escalations", Icon: AlertTriangle,   href: "/escalations"  },
  { label: "Reports",     Icon: BarChart2,       href: "/reports"      },
];

/* ─── Sidebar ────────────────────────────────────────────────────────────────── */
function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();

  return (
    <aside className={cn("sidebar border-r border-[#E6E0D4] bg-[#FCFBF8]", open && "open")}>
      {/* Logo */}
      <div className="px-5 py-6 border-b border-[#E6E0D4] bg-white">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#1F5C57] flex items-center justify-center shrink-0 shadow-sm shadow-[#1F5C57]/20">
            <span className="text-white font-black text-lg">C</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-extrabold text-[#171717] text-sm leading-tight tracking-tight uppercase">CRM Digital</p>
            <p className="text-[10px] text-[#8A847B] font-bold tracking-widest uppercase mt-0.5">Command Center</p>
          </div>
          <button className="menu-toggle md:hidden p-1.5" onClick={onClose} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Nav */}
      <nav className="p-3 flex-1 flex flex-col gap-6 mt-4">
        <div>
          <p className="text-[10px] font-bold text-[#8A847B] uppercase tracking-[0.12em] px-3 mb-3">
            Workspace
          </p>
          <div className="flex flex-col gap-1">
            {NAV.map(({ label, Icon, href }) => {
              const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link 
                  key={label} 
                  href={href} 
                  className={cn("nav-item group", active && "active")} 
                  onClick={onClose}
                >
                  <Icon size={16} strokeWidth={active ? 2.5 : 2} className={cn("transition-colors", active ? "text-[#1F5C57]" : "text-[#8A847B] group-hover:text-[#5F5A52]")} />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>

        <div>
          <p className="text-[10px] font-bold text-[#8A847B] uppercase tracking-[0.12em] px-3 mb-3">
            System
          </p>
          <div className="flex flex-col gap-1">
            <Link 
              href="/support" 
              className={cn("nav-item group", pathname === "/support" && "active")} 
              onClick={onClose}
            >
              <Globe size={16} strokeWidth={pathname === "/support" ? 2.5 : 2} className={cn(pathname === "/support" ? "text-[#1F5C57]" : "text-[#8A847B] group-hover:text-[#5F5A52]")} />
              Support Form
            </Link>
            <Link 
              href="/settings" 
              className={cn("nav-item group", pathname === "/settings" && "active")} 
              onClick={onClose}
            >
              <Settings size={16} strokeWidth={pathname === "/settings" ? 2.5 : 2} className={cn(pathname === "/settings" ? "text-[#1F5C57]" : "text-[#8A847B] group-hover:text-[#5F5A52]")} />
              Settings
            </Link>
          </div>
        </div>
      </nav>

      {/* Bottom user */}
      <div className="p-4 border-t border-[#E6E0D4] bg-white">
        <div
          className="flex items-center gap-3 cursor-pointer rounded-xl p-2 hover:bg-[#F6F4EF] transition-all group"
        >
          <div className="w-9 h-9 rounded-full bg-[#E7F1EF] flex items-center justify-center shrink-0 border border-[#D7D0C2]">
            <span className="text-[13px] font-bold text-[#174944]">A</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-bold text-[#171717] truncate leading-tight">Admin User</p>
            <p className="text-[11px] text-[#8A847B] font-medium truncate">admin@crmdigital.io</p>
          </div>
          <ChevronDown size={14} className="text-[#8A847B] group-hover:text-[#5F5A52]" />
        </div>
      </div>
    </aside>
  );
}

/* ─── Top bar ────────────────────────────────────────────────────────────────── */
function TopBar({ ticketCount, onMenuClick }: { ticketCount: number; onMenuClick: () => void }) {
  return (
    <header className="topbar px-6 md:px-8 border-b border-[#E6E0D4] bg-white sticky top-0 z-30 flex items-center gap-6 h-16">
      <button className="menu-toggle md:hidden" onClick={onMenuClick} aria-label="Open menu">
        <Menu size={20} />
      </button>
      
      <div className="flex-1">
        <div className="relative max-w-xl group">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <Search size={15} className="text-[#8A847B] group-focus-within:text-[#1F5C57] transition-colors" />
          </div>
          <input 
            placeholder="Search tickets, customers, commands…" 
            className="w-full bg-[#F6F4EF] border border-[#E6E0D4] rounded-xl pl-10 pr-12 py-2 text-[13.5px] font-medium text-[#171717] placeholder:text-[#8A847B] focus:outline-none focus:ring-2 focus:ring-[#1F5C57]/10 focus:border-[#1F5C57] transition-all"
          />
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center gap-1.5">
            <div className="hidden sm:flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-white border border-[#E6E0D4] shadow-sm">
              <Command size={10} className="text-[#8A847B]" />
              <span className="text-[10px] font-bold text-[#8A847B]">K</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-[#E6E0D4] text-[#5F5A52] hover:bg-[#F6F4EF] transition-all relative">
          <Bell size={18} />
          {ticketCount > 0 && (
            <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#A04646] ring-2 ring-white animate-pulse" />
          )}
        </button>
        <div className="w-10 h-10 rounded-xl bg-[#1F5C57] flex items-center justify-center cursor-pointer shadow-sm hover:opacity-90 transition-opacity">
          <span className="text-[13px] font-bold text-white">A</span>
        </div>
      </div>
    </header>
  );
}

/* ─── Shell wrapper ──────────────────────────────────────────────────────────── */
export function Shell({ children, ticketCount = 0 }: { children: React.ReactNode; ticketCount?: number }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell min-h-screen bg-[#F6F4EF]">
      <div 
        className={cn("sidebar-overlay z-40 backdrop-blur-[1px] bg-black/20 transition-opacity", sidebarOpen && "open")} 
        onClick={() => setSidebarOpen(false)} 
      />
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-area flex-1 flex flex-col min-w-0">
        <TopBar ticketCount={ticketCount} onMenuClick={() => setSidebarOpen(o => !o)} />
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
