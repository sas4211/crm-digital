"use client";

import { Circle, ShieldAlert, CheckCircle2, TrendingUp, TrendingDown } from "lucide-react";
import { Ticket, Health, DailyReport as DailyReportType } from "@/app/lib/types";
import { timeAgo, cn } from "@/app/lib/utils";

export function AgentStatus({ health, loading }: { health: Health | null; loading: boolean }) {
  return (
    <div className="card">
      <div className="card-header">
        <p className="text-[13.5px] font-bold text-[#171717]">Agent Alex</p>
        {!loading && (
          <span className={cn("chip", health ? "chip-ok" : "chip-danger")}>
            <Circle size={6} fill="currentColor" />
            {health ? "Online" : "Offline"}
          </span>
        )}
      </div>
      <div className="p-[14px] px-5">
        {loading ? (
          <div className="skeleton h-10 w-full" />
        ) : health ? (
          <div className="flex flex-col gap-2.5">
            <div className="flex justify-between items-center">
              <span className="text-[12.5px] text-[#8A847B] font-medium">Model</span>
              <span className="text-[12.5px] font-bold text-[#171717] mono">{health.model}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[12.5px] text-[#8A847B] font-medium">Channels</span>
              <span className="text-[12.5px] font-bold text-[#171717]">Email · WhatsApp · Web</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[12.5px] text-[#8A847B] font-medium">Response SLA</span>
              <span className="text-[12.5px] font-bold text-[#2E6A4F]">{"< 30s"}</span>
            </div>
          </div>
        ) : (
          <p className="text-[13px] text-[#A04646] font-medium">Backend unreachable. Start the FastAPI server.</p>
        )}
      </div>
    </div>
  );
}

export function EscalationQueue({ tickets, loading, onTicketClick }: { tickets: Ticket[]; loading: boolean; onTicketClick: (t: Ticket) => void }) {
  const escalated = tickets.filter(t => t.status === "escalated");

  return (
    <div className="card">
      <div className="card-header">
        <p className="text-[13.5px] font-bold text-[#171717]">Escalation Queue</p>
        {!loading && escalated.length > 0 && (
          <span className="chip chip-danger">{escalated.length}</span>
        )}
      </div>
      <div className="divide-y divide-[#E6E0D4]">
        {loading ? (
          <div className="p-4 flex flex-col gap-3">
            {[1, 2].map(i => <div key={i} className="skeleton h-[52px] w-full" />)}
          </div>
        ) : escalated.length === 0 ? (
          <div className="p-7 px-5 text-center">
            <CheckCircle2 size={20} className="text-[#2E6A4F] mx-auto mb-2" />
            <p className="text-[13px] text-[#2E6A4F] font-bold">All clear</p>
            <p className="text-[12px] text-[#8A847B] mt-0.5">No active escalations</p>
          </div>
        ) : (
          escalated.map((t) => (
            <div
              key={t.id}
              onClick={() => onTicketClick(t)}
              className="p-3 px-5 hover:bg-[#F6F4EF] cursor-pointer transition-colors group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-width-0">
                  <p className="text-[13px] font-bold text-[#171717] truncate group-hover:text-[#1F5C57]">
                    {t.subject}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[11px] text-[#8A847B] font-medium">{timeAgo(t.created_at)}</span>
                    <span className="text-[11px] text-[#A04646] font-bold">
                      {t.priority === "critical" ? "Critical" : "High"}
                    </span>
                  </div>
                </div>
                <ShieldAlert size={14} className="text-[#A04646] shrink-0 mt-0.5" />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function DailyReport({ report, loading }: { report: DailyReportType | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="card">
        <div className="card-header"><p className="text-[13.5px] font-bold text-[#171717]">Daily Report</p></div>
        <div className="p-4 flex flex-col gap-3">
          {[100, 85, 70, 90].map((w, i) => <div key={i} className="skeleton h-3.5" style={{ width: `${w}%` }} />)}
        </div>
      </div>
    );
  }
  if (!report) return null;

  const rate = report.total_tickets > 0
    ? Math.round((report.resolved / report.total_tickets) * 100)
    : 0;

  const narrative = report.summary_text ?? report.summary;
  const issues = Array.isArray(report.top_issues) ? report.top_issues : [];

  return (
    <div className="card">
      <div className="card-header">
        <p className="text-[13.5px] font-bold text-[#171717]">Today&apos;s Summary</p>
        <span className="text-[12px] text-[#8A847B] font-medium">
          {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" })}
        </span>
      </div>
      
      <div className="p-4 px-5 border-b border-[#E6E0D4] bg-gradient-to-b from-white to-[#FCFBF8]">
        <div className="flex justify-between items-center mb-2.5">
          <span className="text-[12.5px] text-[#8A847B] font-medium">Resolution rate</span>
          <div className="flex items-center gap-1.5">
            {rate >= 80 ? <TrendingUp size={14} className="text-[#2E6A4F]" /> : <TrendingDown size={14} className="text-[#A56A18]" />}
            <span className={cn("text-[13px] font-bold", rate >= 80 ? "text-[#2E6A4F]" : "text-[#A56A18]")}>{rate}%</span>
          </div>
        </div>
        <div className="h-1.5 bg-[#F6F4EF] rounded-full overflow-hidden border border-[#E6E0D4]">
          <div 
            className={cn("h-full rounded-full transition-all duration-1000 ease-out", rate >= 80 ? "bg-[#2E6A4F]" : "bg-[#A56A18]")}
            style={{ width: `${rate}%` }}
          />
        </div>
        <div className="flex justify-between mt-2.5">
          <span className="text-[11px] text-[#8A847B] font-medium">{report.resolved} resolved of {report.total_tickets}</span>
          {report.avg_sentiment !== null && (
            <span className="text-[11px] text-[#8A847B] font-medium">
              Sentiment: <strong className={report.avg_sentiment >= 0 ? "text-[#2E6A4F]" : "text-[#A04646]"}>{report.avg_sentiment.toFixed(2)}</strong>
            </span>
          )}
        </div>
      </div>

      {narrative && (
        <div className={cn("p-4 px-5 text-[13px] text-[#5F5A52] leading-relaxed", issues.length > 0 && "border-b border-[#E6E0D4]")}>
          {narrative}
        </div>
      )}

      {issues.length > 0 && (
        <div className="p-3 px-5">
          <p className="text-[10px] font-bold text-[#8A847B] uppercase tracking-wider mb-2.5">
            Top Keywords
          </p>
          <div className="flex flex-col gap-2">
            {issues.slice(0, 5).map((issue, i) => (
              <div key={i} className="flex gap-2.5 items-center justify-between">
                <div className="flex gap-2.5 items-center truncate">
                  <span className="w-5 h-5 rounded bg-[#F6F4EF] text-[#8A847B] text-[10px] font-bold flex items-center justify-center mono shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-[12.5px] text-[#5F5A52] font-medium truncate capitalize">{issue.keyword}</span>
                </div>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#F6F4EF] text-[#8A847B] border border-[#E6E0D4]">
                  {issue.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
