"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowUpRight, RefreshCw } from "lucide-react";
import { Shell } from "./components/Shell";
import { Ticket, DailyReport as DailyReportType, Health } from "./lib/types";
import { KPIGrid } from "./components/dashboard/KPICards";
import { AttentionTable, AllTickets } from "./components/dashboard/TicketTables";
import { ChannelChart } from "./components/dashboard/Charts";
import { AgentStatus, EscalationQueue, DailyReport } from "./components/dashboard/AgentMonitor";
import { TicketDetail } from "./components/dashboard/TicketDetail";

export default function Dashboard() {
  const [tickets, setTickets]   = useState<Ticket[]>([]);
  const [report, setReport]     = useState<DailyReportType | null>(null);
  const [health, setHealth]     = useState<Health | null>(null);
  const [loading, setLoading]   = useState(true);
  const [backendDown, setBackendDown] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  
  // Interaction state
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch("/api/tickets").then(r => r.json()),
      fetch("/api/reports/daily").then(r => r.json()),
      fetch("/api/health").then(r => r.json()),
    ])
      .then(([t, r, h]) => {
        setTickets(Array.isArray(t) ? t : (t.tickets ?? []));
        setReport(r ?? null);
        setHealth(h ?? null);
        setLastRefresh(new Date());
        setBackendDown(false);
      })
      .catch(() => setBackendDown(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const escalatedCount = tickets.filter(t => t.status === "escalated").length;
  const openCount      = tickets.filter(t => t.status === "open" || t.status === "in_progress").length;

  return (
    <Shell ticketCount={escalatedCount}>
      <main className="p-7 pb-12 max-w-[1600px] mx-auto">
          {/* Backend error */}
          {backendDown && !loading && (
            <div className="mb-5 p-3 px-4 rounded-xl bg-[#F8E6E6] border border-[#f0c8c8] flex items-center gap-2 text-[13px] text-[#A04646] font-medium animate-in fade-in slide-in-from-top-2 duration-300">
              <AlertTriangle size={14} />
              Backend unavailable — start the FastAPI server, then refresh.
            </div>
          )}

          {/* Page header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-[#171717] leading-tight">
                Operations Dashboard
              </h1>
              <p className="text-[13px] text-[#8A847B] mt-1 font-medium">
                {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                {!loading && (
                  <span className="ml-1.5 pl-1.5 border-l border-[#E6E0D4]">
                    Last updated {lastRefresh.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2.5">
              <button className="btn-secondary h-10 px-4 flex items-center gap-2" onClick={load}>
                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                Refresh
              </button>
              <Link href="/support" className="btn-primary h-10 px-4 flex items-center gap-2">
                <ArrowUpRight size={14} />
                Open Support Form
              </Link>
            </div>
          </div>

          {/* KPI row */}
          <KPIGrid 
            report={report} 
            openCount={openCount} 
            escalatedCount={escalatedCount} 
            totalCount={tickets.length}
            loading={loading} 
          />

          {/* Main grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left column */}
            <div className="lg:col-span-8 flex flex-col gap-6 min-w-0">
              <AttentionTable 
                tickets={tickets} 
                loading={loading} 
                onTicketClick={setSelectedTicket} 
              />
              <AllTickets     
                tickets={tickets} 
                loading={loading} 
                onTicketClick={setSelectedTicket}
              />
              <ChannelChart   
                tickets={tickets} 
                loading={loading} 
              />
            </div>

            {/* Right column */}
            <div className="lg:col-span-4 flex flex-col gap-6">
              <AgentStatus    health={health}   loading={loading} />
              <EscalationQueue 
                tickets={tickets} 
                loading={loading} 
                onTicketClick={setSelectedTicket}
              />
              <DailyReport    report={report}   loading={loading} />
            </div>
          </div>
      </main>

      {/* Ticket Detail Slide-over */}
      <TicketDetail 
        ticket={selectedTicket} 
        onClose={() => setSelectedTicket(null)} 
      />
    </Shell>
  );
}
