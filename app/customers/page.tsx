"use client";

import { useEffect, useState } from "react";
import { Search, RefreshCw, Users, Ticket, Building2 } from "lucide-react";
import { Shell } from "../components/Shell";

interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  company: string | null;
  plan: string;
  ticket_count: number;
  open_tickets: number;
  last_activity: string | null;
  created_at: string | null;
}

const PLAN_STYLE: Record<string, { label: string; cls: string }> = {
  free:       { label: "Free",       cls: "chip-neutral" },
  starter:    { label: "Starter",    cls: "chip-info"    },
  pro:        { label: "Pro",        cls: "chip-primary" },
  enterprise: { label: "Enterprise", cls: "chip-ok"      },
};

function timeAgo(iso: string | null) {
  if (!iso) return "—";
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (d < 1)  return "just now";
  if (d < 60) return `${d}m ago`;
  const h = Math.floor(d / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function Avatar({ name }: { name: string }) {
  const initials = name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div style={{
      width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
      background: "var(--p-soft)", display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <span style={{ fontSize: 12, fontWeight: 700, color: "var(--p-text)" }}>{initials}</span>
    </div>
  );
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState("");
  const [planFilter, setPlanFilter] = useState("all");

  const load = () => {
    setLoading(true);
    fetch("/api/customers")
      .then(r => r.json())
      .then(d => setCustomers(Array.isArray(d) ? d : (d.customers ?? [])))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const filtered = customers.filter(c => {
    if (planFilter !== "all" && c.plan !== planFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return c.name.toLowerCase().includes(q) ||
             c.email.toLowerCase().includes(q) ||
             (c.company ?? "").toLowerCase().includes(q);
    }
    return true;
  });

  const plans = ["all", ...Array.from(new Set(customers.map(c => c.plan)))];

  return (
    <Shell>
      <main style={{ padding: "28px 28px 48px" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Customers</h1>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 3 }}>
              {loading ? "Loading…" : `${customers.length} total · ${filtered.length} shown`}
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
              { label: "Total Customers", value: customers.length,                                                Icon: Users    },
              { label: "With Open Tickets", value: customers.filter(c => c.open_tickets > 0).length,             Icon: Ticket   },
              { label: "Companies",         value: new Set(customers.map(c => c.company).filter(Boolean)).size,   Icon: Building2},
            ].map(({ label, value, Icon }) => (
              <div key={label} className="card fade-up" style={{ padding: "18px 20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                  <p style={{ fontSize: 12, fontWeight: 600, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
                  <Icon size={14} color="var(--text-3)" strokeWidth={1.8} />
                </div>
                <p style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
          <div className="search-input" style={{ flex: "0 0 240px" }}>
            <Search size={13} color="var(--text-3)" />
            <input
              placeholder="Search name, email, company…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {plans.map(p => (
              <button
                key={p}
                onClick={() => setPlanFilter(p)}
                style={{
                  padding: "4px 10px", borderRadius: 7, border: "1px solid",
                  fontSize: 12.5, fontWeight: 500, cursor: "pointer", transition: "all 0.12s",
                  background: planFilter === p ? "var(--p-soft)" : "transparent",
                  color: planFilter === p ? "var(--p-text)" : "var(--text-2)",
                  borderColor: planFilter === p ? "var(--p-soft)" : "var(--border)",
                  textTransform: "capitalize",
                }}
              >
                {p === "all" ? "All plans" : p}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="card fade-up">
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Company</th>
                  <th>Plan</th>
                  <th>Tickets</th>
                  <th>Open</th>
                  <th>Last activity</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {[200, 130, 70, 50, 50, 80].map((w, j) => (
                        <td key={j}><div className="skeleton" style={{ height: 14, width: w }} /></td>
                      ))}
                    </tr>
                  ))
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: "center", padding: "40px", color: "var(--text-3)" }}>
                      {customers.length === 0 ? "No customers yet — tickets will create customers automatically." : "No customers match your search."}
                    </td>
                  </tr>
                ) : (
                  filtered.map(c => {
                    const plan = PLAN_STYLE[c.plan] ?? { label: c.plan, cls: "chip-neutral" };
                    return (
                      <tr key={c.id} style={{ cursor: "pointer" }}>
                        <td>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <Avatar name={c.name} />
                            <div>
                              <p style={{ fontWeight: 600, fontSize: 13.5 }}>{c.name}</p>
                              <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 1 }}>{c.email}</p>
                            </div>
                          </div>
                        </td>
                        <td style={{ color: "var(--text-2)", fontSize: 13 }}>{c.company || "—"}</td>
                        <td><span className={`chip ${plan.cls}`}>{plan.label}</span></td>
                        <td style={{ fontWeight: 600 }}>{c.ticket_count}</td>
                        <td>
                          {c.open_tickets > 0
                            ? <span className="chip chip-warn">{c.open_tickets}</span>
                            : <span style={{ color: "var(--text-3)", fontSize: 13 }}>—</span>
                          }
                        </td>
                        <td style={{ color: "var(--text-3)", fontSize: 13, whiteSpace: "nowrap" }}>{timeAgo(c.last_activity)}</td>
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
