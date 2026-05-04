"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, RefreshCw, CheckCircle2, Clock, Mail, MessageCircle, Globe, AlertTriangle } from "lucide-react";
import { Shell } from "../components/Shell";

interface Ticket {
  id: string;
  subject: string;
  status: "open" | "in_progress" | "waiting_customer" | "escalated" | "resolved" | "closed";
  channel: "email" | "whatsapp" | "web_form";
  priority: "low" | "medium" | "high" | "critical";
  sentiment: number | null;
  created_at: string;
  customer_id?: string;
}

const CHANNEL: Record<Ticket["channel"], { label: string; Icon: React.ElementType }> = {
  email:    { label: "Email",    Icon: Mail          },
  whatsapp: { label: "WhatsApp", Icon: MessageCircle },
  web_form: { label: "Web",      Icon: Globe         },
};

function timeAgo(iso: string) {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (d < 1)  return "just now";
  if (d < 60) return `${d}m ago`;
  const h = Math.floor(d / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function sentimentLabel(s: number | null) {
  if (s === null) return { label: "—", cls: "chip-neutral" };
  if (s >= 0.4)  return { label: "Positive", cls: "chip-ok"    };
  if (s >= -0.1) return { label: "Neutral",  cls: "chip-neutral" };
  if (s >= -0.5) return { label: "Negative", cls: "chip-warn"  };
  return               { label: "Critical",  cls: "chip-danger" };
}

function queueTime(iso: string) {
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return { text: `${mins}m`, urgent: mins > 30 };
  const hrs = Math.floor(mins / 60);
  return { text: `${hrs}h ${mins % 60}m`, urgent: hrs >= 1 };
}

export default function EscalationsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetch("/api/tickets?status=escalated&limit=100")
      .then(r => r.json())
      .then(d => {
        const all = Array.isArray(d) ? d : (d.tickets ?? []);
        setTickets(all.filter((t: Ticket) => t.status === "escalated"));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const critical = tickets.filter(t => t.priority === "critical");
  const high     = tickets.filter(t => t.priority === "high");
  const other    = tickets.filter(t => t.priority !== "critical" && t.priority !== "high");

  return (
    <Shell>
      <main style={{ padding: "28px 28px 48px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Escalations</h1>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 3 }}>
              {loading ? "Loading…" : tickets.length === 0 ? "No active escalations" : `${tickets.length} ticket${tickets.length !== 1 ? "s" : ""} need human review`}
            </p>
          </div>
          <button className="btn-secondary" onClick={load} style={{ gap: 6 }}>
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>

        {/* KPI strip */}
        {!loading && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 24 }}>
            {[
              { label: "Total Escalated", value: tickets.length,   color: tickets.length > 0 ? "var(--danger)" : undefined, Icon: ShieldAlert   },
              { label: "Critical",        value: critical.length,  color: critical.length > 0 ? "var(--danger)" : undefined, Icon: AlertTriangle },
              { label: "High Priority",   value: high.length,      color: high.length > 0 ? "var(--warn)" : undefined,       Icon: Clock         },
            ].map(({ label, value, color, Icon }) => (
              <div key={label} className="card fade-up" style={{ padding: "18px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                  <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
                  <Icon size={14} color="var(--text-3)" strokeWidth={1.8} />
                </div>
                <p style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", color: color ?? "var(--text-1)" }}>{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* All clear */}
        {!loading && tickets.length === 0 && (
          <div className="card fade-up" style={{ padding: "56px 24px", textAlign: "center" }}>
            <CheckCircle2 size={36} color="var(--ok)" style={{ margin: "0 auto 12px" }} />
            <p style={{ fontSize: 15, fontWeight: 600, color: "var(--ok)" }}>All clear</p>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 4 }}>No active escalations — Agent Alex is handling everything.</p>
          </div>
        )}

        {/* Ticket cards */}
        {(loading || tickets.length > 0) && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="card" style={{ padding: 20 }}>
                  <div className="skeleton" style={{ height: 16, width: "60%", marginBottom: 10 }} />
                  <div className="skeleton" style={{ height: 12, width: "40%" }} />
                </div>
              ))
            ) : (
              [...critical, ...high, ...other].map(t => {
                const ch = CHANNEL[t.channel];
                const sm = sentimentLabel(t.sentiment);
                const qt = queueTime(t.created_at);
                return (
                  <div key={t.id} className="card fade-up" style={{
                    padding: "18px 20px",
                    borderLeft: `3px solid ${t.priority === "critical" ? "var(--danger)" : t.priority === "high" ? "var(--warn)" : "var(--border)"}`,
                  }}>
                    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                          <ShieldAlert size={14} color="var(--danger)" />
                          <p style={{ fontSize: 14, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {t.subject}
                          </p>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                          <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12.5, color: "var(--text-3)" }}>
                            <ch.Icon size={12} strokeWidth={1.8} />{ch.label}
                          </span>
                          {t.customer_id && (
                            <span className="mono" style={{ fontSize: 11.5, color: "var(--text-3)" }}>{t.customer_id.slice(0, 8)}</span>
                          )}
                          <span className={`chip ${sm.cls}`} style={{ fontSize: 11.5 }}>{sm.label}</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, flexShrink: 0 }}>
                        <span style={{
                          fontSize: 12, fontWeight: 700,
                          color: t.priority === "critical" ? "var(--danger)" : t.priority === "high" ? "var(--warn)" : "var(--text-2)",
                          textTransform: "uppercase", letterSpacing: "0.04em",
                        }}>
                          {t.priority}
                        </span>
                        <span style={{ fontSize: 12, color: qt.urgent ? "var(--danger)" : "var(--text-3)", fontWeight: qt.urgent ? 600 : 400 }}>
                          In queue: {qt.text}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </main>
    </Shell>
  );
}
