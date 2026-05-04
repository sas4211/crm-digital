"use client";

import { useEffect, useState } from "react";
import { Mail, MessageCircle, Globe, Search, RefreshCw, Filter } from "lucide-react";
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

const STATUS: Record<Ticket["status"], { label: string; cls: string }> = {
  open:             { label: "Open",          cls: "chip-warn"    },
  in_progress:      { label: "In Progress",   cls: "chip-info"    },
  waiting_customer: { label: "Waiting",       cls: "chip-neutral" },
  escalated:        { label: "Escalated",     cls: "chip-danger"  },
  resolved:         { label: "Resolved",      cls: "chip-ok"      },
  closed:           { label: "Closed",        cls: "chip-neutral" },
};

const PRIORITY: Record<Ticket["priority"], { label: string; color: string }> = {
  low:      { label: "Low",      color: "var(--text-3)"  },
  medium:   { label: "Medium",   color: "var(--warn)"    },
  high:     { label: "High",     color: "var(--danger)"  },
  critical: { label: "Critical", color: "var(--danger)"  },
};

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
  if (s >= 0.4)  return { label: "Positive", cls: "chip-ok"      };
  if (s >= -0.1) return { label: "Neutral",  cls: "chip-neutral" };
  if (s >= -0.5) return { label: "Negative", cls: "chip-warn"    };
  return               { label: "Critical",  cls: "chip-danger"  };
}

const STATUS_FILTERS = [
  { key: "all",             label: "All"         },
  { key: "open",            label: "Open"        },
  { key: "in_progress",     label: "Active"      },
  { key: "waiting_customer",label: "Waiting"     },
  { key: "escalated",       label: "Escalated"   },
  { key: "resolved",        label: "Resolved"    },
  { key: "closed",          label: "Closed"      },
];

const CHANNEL_FILTERS = [
  { key: "all",      label: "All channels" },
  { key: "email",    label: "Email"        },
  { key: "whatsapp", label: "WhatsApp"     },
  { key: "web_form", label: "Web Form"     },
];

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter]   = useState("all");
  const [channelFilter, setChannelFilter] = useState("all");
  const [search, setSearch] = useState("");

  const load = () => {
    setLoading(true);
    fetch("/api/tickets?limit=200")
      .then(r => r.json())
      .then(d => setTickets(Array.isArray(d) ? d : (d.tickets ?? [])))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const filtered = tickets.filter(t => {
    if (statusFilter !== "all"  && t.status  !== statusFilter)  return false;
    if (channelFilter !== "all" && t.channel !== channelFilter) return false;
    if (search && !t.subject.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const counts: Record<string, number> = { all: tickets.length };
  tickets.forEach(t => { counts[t.status] = (counts[t.status] ?? 0) + 1; });

  return (
    <Shell>
      <main style={{ padding: "28px 28px 48px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Tickets</h1>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 3 }}>
              {loading ? "Loading…" : `${tickets.length} total · ${filtered.length} shown`}
            </p>
          </div>
          <button className="btn-secondary" onClick={load} style={{ gap: 6 }}>
            <RefreshCw size={13} />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap", alignItems: "center" }}>
          {/* Search */}
          <div className="search-input" style={{ flex: "0 0 220px" }}>
            <Search size={13} color="var(--text-3)" />
            <input
              placeholder="Search subjects…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>

          {/* Status pills */}
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {STATUS_FILTERS.map(f => (
              <button
                key={f.key}
                onClick={() => setStatusFilter(f.key)}
                style={{
                  padding: "4px 10px", borderRadius: 7, border: "1px solid",
                  fontSize: 12.5, fontWeight: 500, cursor: "pointer", transition: "all 0.12s",
                  background: statusFilter === f.key ? "var(--p-soft)" : "transparent",
                  color: statusFilter === f.key ? "var(--p-text)" : "var(--text-2)",
                  borderColor: statusFilter === f.key ? "var(--p-soft)" : "var(--border)",
                }}
              >
                {f.label}{counts[f.key] !== undefined ? ` (${counts[f.key]})` : ""}
              </button>
            ))}
          </div>

          {/* Channel filter */}
          <select
            value={channelFilter}
            onChange={e => setChannelFilter(e.target.value)}
            style={{
              padding: "5px 10px", borderRadius: 7, border: "1px solid var(--border)",
              fontSize: 12.5, background: "var(--surface-hi)", color: "var(--text-2)",
              cursor: "pointer", fontFamily: "inherit",
            }}
          >
            {CHANNEL_FILTERS.map(f => (
              <option key={f.key} value={f.key}>{f.label}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="card fade-up">
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Channel</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Sentiment</th>
                  <th>Opened</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {[280, 80, 90, 70, 80, 70].map((w, j) => (
                        <td key={j}><div className="skeleton" style={{ height: 14, width: w }} /></td>
                      ))}
                    </tr>
                  ))
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "40px", color: "var(--text-3)" }}>
                      No tickets match your filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map(t => {
                    const st = STATUS[t.status];
                    const pr = PRIORITY[t.priority];
                    const ch = CHANNEL[t.channel];
                    const sm = sentimentLabel(t.sentiment);
                    return (
                      <tr key={t.id} style={{ cursor: "pointer" }}>
                        <td style={{ maxWidth: 320 }}>
                          <p style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 300 }}>
                            {t.subject}
                          </p>
                          {t.customer_id && (
                            <p style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 1 }} className="mono">
                              {t.customer_id.slice(0, 8)}
                            </p>
                          )}
                        </td>
                        <td>
                          <span style={{ display: "flex", alignItems: "center", gap: 5, color: "var(--text-2)", fontSize: 13 }}>
                            <ch.Icon size={13} strokeWidth={1.8} />{ch.label}
                          </span>
                        </td>
                        <td><span className={`chip ${st.cls}`}>{st.label}</span></td>
                        <td><span style={{ fontSize: 13, fontWeight: 600, color: pr.color }}>{pr.label}</span></td>
                        <td><span className={`chip ${sm.cls}`}>{sm.label}</span></td>
                        <td style={{ color: "var(--text-3)", fontSize: 13, whiteSpace: "nowrap" }}>{timeAgo(t.created_at)}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </Shell>
  );
}
