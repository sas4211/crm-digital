"use client";

import { useEffect, useState } from "react";
import { RefreshCw, CheckCircle2, AlertTriangle, TrendingUp, BarChart2, Mail, MessageCircle, Globe } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from "recharts";
import { Shell } from "../components/Shell";

interface DailyReport {
  total_tickets: number;
  resolved: number;
  escalated: number;
  avg_sentiment: number | null;
  top_issues: string[];
  summary?: string;
  summary_text?: string;
}

interface Ticket {
  id: string;
  status: string;
  channel: string;
  priority: string;
  sentiment: number | null;
  created_at: string;
}

function StatCard({ label, value, sub, color, Icon }: {
  label: string; value: string | number; sub?: string;
  color?: string; Icon?: React.ElementType;
}) {
  return (
    <div className="card fade-up" style={{ padding: "20px 22px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
        {Icon && <Icon size={15} color="var(--text-3)" strokeWidth={1.8} />}
      </div>
      <p style={{ fontSize: 30, fontWeight: 700, letterSpacing: "-0.02em", color: color ?? "var(--text-1)" }}>{value}</p>
      {sub && <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 6 }}>{sub}</p>}
    </div>
  );
}

const CHART_COLORS = ["var(--p)", "var(--ok)", "var(--warn)", "var(--danger)", "var(--info)"];

export default function ReportsPage() {
  const [report, setReport]   = useState<DailyReport | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      fetch("/api/reports/daily").then(r => r.json()),
      fetch("/api/tickets?limit=200").then(r => r.json()),
    ])
      .then(([r, t]) => {
        setReport(r ?? null);
        setTickets(Array.isArray(t) ? t : (t.tickets ?? []));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  /* Derived chart data */
  const byStatus = [
    { name: "Open",        count: tickets.filter(t => t.status === "open").length,             fill: "var(--warn)"   },
    { name: "Active",      count: tickets.filter(t => t.status === "in_progress").length,      fill: "var(--info)"   },
    { name: "Waiting",     count: tickets.filter(t => t.status === "waiting_customer").length, fill: "var(--text-3)" },
    { name: "Escalated",   count: tickets.filter(t => t.status === "escalated").length,        fill: "var(--danger)" },
    { name: "Resolved",    count: tickets.filter(t => t.status === "resolved").length,         fill: "var(--ok)"     },
    { name: "Closed",      count: tickets.filter(t => t.status === "closed").length,           fill: "var(--border-strong)" },
  ].filter(d => d.count > 0);

  const byChannel = [
    { name: "Email",    value: tickets.filter(t => t.channel === "email").length    },
    { name: "WhatsApp", value: tickets.filter(t => t.channel === "whatsapp").length },
    { name: "Web Form", value: tickets.filter(t => t.channel === "web_form").length },
  ].filter(d => d.value > 0);

  const byPriority = [
    { name: "Low",      count: tickets.filter(t => t.priority === "low").length,      fill: "var(--text-3)"  },
    { name: "Medium",   count: tickets.filter(t => t.priority === "medium").length,   fill: "var(--warn)"    },
    { name: "High",     count: tickets.filter(t => t.priority === "high").length,     fill: "var(--danger)"  },
    { name: "Critical", count: tickets.filter(t => t.priority === "critical").length, fill: "var(--danger)"  },
  ].filter(d => d.count > 0);

  const rate = report && report.total_tickets > 0
    ? Math.round((report.resolved / report.total_tickets) * 100)
    : 0;

  const narrative = report?.summary_text ?? report?.summary;
  const issues: string[] = Array.isArray(report?.top_issues) ? report!.top_issues : [];

  return (
    <Shell>
      <main style={{ padding: "28px 28px 48px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Reports</h1>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 3 }}>
              {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </p>
          </div>
          <button className="btn-secondary" onClick={load} style={{ gap: 6 }}>
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>

        {/* KPI row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 24 }}>
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="card" style={{ padding: "20px 22px" }}>
                <div className="skeleton" style={{ height: 12, width: 80, marginBottom: 12 }} />
                <div className="skeleton" style={{ height: 32, width: 60 }} />
              </div>
            ))
          ) : (
            <>
              <StatCard label="Total Tickets"     value={report?.total_tickets ?? tickets.length} Icon={BarChart2}    />
              <StatCard label="Resolved Today"    value={report?.resolved ?? 0}                   Icon={CheckCircle2} color="var(--ok)"     sub={`${rate}% resolution rate`} />
              <StatCard label="Escalated"         value={report?.escalated ?? 0}                  Icon={AlertTriangle} color={report?.escalated ? "var(--danger)" : undefined} />
              <StatCard
                label="Avg Sentiment"
                value={report?.avg_sentiment != null ? report.avg_sentiment.toFixed(2) : "—"}
                Icon={TrendingUp}
                color={report?.avg_sentiment != null ? (report.avg_sentiment >= 0 ? "var(--ok)" : "var(--danger)") : undefined}
              />
            </>
          )}
        </div>

        {/* Charts row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          {/* Tickets by status */}
          <div className="card fade-up">
            <div className="card-header">
              <p style={{ fontSize: 13.5, fontWeight: 600 }}>Tickets by Status</p>
            </div>
            <div style={{ padding: "20px 16px 16px" }}>
              {loading ? (
                <div className="skeleton" style={{ height: 180 }} />
              ) : byStatus.length === 0 ? (
                <p style={{ textAlign: "center", color: "var(--text-3)", fontSize: 13, padding: "40px 0" }}>No data</p>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={byStatus} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--text-3)" }} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-3)" }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ fontSize: 12, background: "var(--surface-hi)", border: "1px solid var(--border)", borderRadius: 8 }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {byStatus.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Tickets by priority */}
          <div className="card fade-up">
            <div className="card-header">
              <p style={{ fontSize: 13.5, fontWeight: 600 }}>Tickets by Priority</p>
            </div>
            <div style={{ padding: "20px 16px 16px" }}>
              {loading ? (
                <div className="skeleton" style={{ height: 180 }} />
              ) : byPriority.length === 0 ? (
                <p style={{ textAlign: "center", color: "var(--text-3)", fontSize: 13, padding: "40px 0" }}>No data</p>
              ) : (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={byPriority} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "var(--text-3)" }} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--text-3)" }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ fontSize: 12, background: "var(--surface-hi)", border: "1px solid var(--border)", borderRadius: 8 }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {byPriority.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* Bottom row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Channel breakdown */}
          <div className="card fade-up">
            <div className="card-header">
              <p style={{ fontSize: 13.5, fontWeight: 600 }}>Channel Breakdown</p>
            </div>
            <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 10 }}>
              {loading ? (
                [80, 55, 65].map((w, i) => <div key={i} className="skeleton" style={{ height: 18, width: `${w}%` }} />)
              ) : (
                [
                  { label: "Email",    count: tickets.filter(t => t.channel === "email").length,    fill: "var(--p)",    Icon: Mail          },
                  { label: "WhatsApp", count: tickets.filter(t => t.channel === "whatsapp").length, fill: "var(--ok)",   Icon: MessageCircle },
                  { label: "Web Form", count: tickets.filter(t => t.channel === "web_form").length, fill: "var(--info)", Icon: Globe         },
                ].map(({ label, count, fill, Icon }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <Icon size={13} color="var(--text-3)" style={{ flexShrink: 0 }} />
                    <p style={{ fontSize: 12.5, color: "var(--text-2)", width: 72, flexShrink: 0 }}>{label}</p>
                    <div style={{ flex: 1, height: 8, background: "var(--bg)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{
                        height: "100%", borderRadius: 4,
                        width: `${tickets.length ? (count / tickets.length) * 100 : 0}%`,
                        background: fill, transition: "width 0.6s cubic-bezier(0.22,1,0.36,1)",
                      }} />
                    </div>
                    <p style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text-2)", width: 24, textAlign: "right" }}>{count}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* AI summary + top issues */}
          <div className="card fade-up">
            <div className="card-header">
              <p style={{ fontSize: 13.5, fontWeight: 600 }}>AI Summary</p>
              <span style={{ fontSize: 12, color: "var(--text-3)" }}>
                {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" })}
              </span>
            </div>
            {loading ? (
              <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                {[100, 85, 70, 90].map((w, i) => <div key={i} className="skeleton" style={{ height: 13, width: `${w}%` }} />)}
              </div>
            ) : !report ? (
              <div style={{ padding: "24px 20px" }}>
                <p style={{ fontSize: 13, color: "var(--text-3)" }}>No report available for today. Reports are generated automatically each day.</p>
              </div>
            ) : (
              <>
                {/* Resolution rate */}
                <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontSize: 12.5, color: "var(--text-3)" }}>Resolution rate</span>
                    <span style={{ fontSize: 12.5, fontWeight: 700, color: rate >= 80 ? "var(--ok)" : "var(--warn)" }}>{rate}%</span>
                  </div>
                  <div style={{ height: 6, background: "var(--bg)", borderRadius: 3, overflow: "hidden", border: "1px solid var(--border)" }}>
                    <div style={{
                      height: "100%", borderRadius: 3, width: `${rate}%`,
                      background: rate >= 80 ? "var(--ok)" : "var(--warn)",
                      transition: "width 0.7s cubic-bezier(0.22,1,0.36,1)",
                    }} />
                  </div>
                </div>
                {narrative && (
                  <div style={{ padding: "14px 20px", borderBottom: issues.length > 0 ? "1px solid var(--border)" : "none" }}>
                    <p style={{ fontSize: 13, color: "var(--text-2)", lineHeight: 1.6 }}>{narrative}</p>
                  </div>
                )}
                {issues.length > 0 && (
                  <div style={{ padding: "12px 20px" }}>
                    <p style={{ fontSize: 11.5, fontWeight: 600, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                      Top Issues
                    </p>
                    <ol style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 5 }}>
                      {issues.slice(0, 5).map((issue, i) => (
                        <li key={i} style={{ display: "flex", gap: 8, fontSize: 12.5, color: "var(--text-2)" }}>
                          <span className="mono" style={{ color: "var(--text-3)", flexShrink: 0 }}>{String(i + 1).padStart(2, "0")}</span>
                          {issue}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </Shell>
  );
}
