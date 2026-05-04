"use client";

import { useState } from "react";
import {
  User, Bot, Bell, Plug, Save, CheckCircle2,
  Mail, MessageCircle, Globe, ChevronRight,
  Shield, Clock, Zap, Volume2, VolumeX,
} from "lucide-react";
import { Shell } from "../components/Shell";

/* ─── Shared primitives ──────────────────────────────────────────────────────── */
function Section({ title, description, children }: {
  title: string; description?: string; children: React.ReactNode;
}) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "0 40px", paddingBottom: 32, borderBottom: "1px solid var(--border)" }}>
      <div style={{ paddingTop: 2 }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-1)" }}>{title}</p>
        {description && <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 4, lineHeight: 1.5 }}>{description}</p>}
      </div>
      <div className="card" style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 18 }}>
        {children}
      </div>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-2)", display: "block", marginBottom: 6 }}>{label}</label>
      {children}
      {hint && <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 5 }}>{hint}</p>}
    </div>
  );
}

function TextInput({ value, onChange, placeholder, type = "text" }: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 9,
        border: "1px solid var(--border)", background: "var(--bg)",
        fontSize: 13.5, color: "var(--text-1)", outline: "none",
        fontFamily: "inherit", transition: "border-color 0.13s",
      }}
      onFocus={e => (e.target.style.borderColor = "var(--p)")}
      onBlur={e => (e.target.style.borderColor = "var(--border)")}
    />
  );
}

function Select({ value, onChange, options }: {
  value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: "100%", padding: "8px 12px", borderRadius: 9,
        border: "1px solid var(--border)", background: "var(--bg)",
        fontSize: 13.5, color: "var(--text-1)", outline: "none",
        fontFamily: "inherit", cursor: "pointer", transition: "border-color 0.13s",
        appearance: "auto",
      }}
      onFocus={e => (e.target.style.borderColor = "var(--p)")}
      onBlur={e => (e.target.style.borderColor = "var(--border)")}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ checked, onChange, label, sub }: {
  checked: boolean; onChange: (v: boolean) => void; label: string; sub?: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
      <div>
        <p style={{ fontSize: 13.5, fontWeight: 500, color: "var(--text-1)" }}>{label}</p>
        {sub && <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 2 }}>{sub}</p>}
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        style={{
          width: 40, height: 22, borderRadius: 11, border: "none",
          background: checked ? "var(--p)" : "var(--border-strong)",
          cursor: "pointer", position: "relative", flexShrink: 0,
          transition: "background 0.18s",
        }}
      >
        <span style={{
          position: "absolute", top: 3,
          left: checked ? 21 : 3,
          width: 16, height: 16, borderRadius: "50%",
          background: "#fff", transition: "left 0.18s",
          boxShadow: "0 1px 3px rgba(0,0,0,0.18)",
        }} />
      </button>
    </div>
  );
}

function ChannelRow({ icon: Icon, label, active, onToggle, status }: {
  icon: React.ElementType; label: string; active: boolean;
  onToggle: () => void; status: string;
}) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 14,
      padding: "14px 16px", borderRadius: 10,
      border: "1px solid var(--border)",
      background: active ? "var(--surface)" : "var(--bg)",
      transition: "border-color 0.13s, background 0.13s",
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 9, flexShrink: 0,
        background: active ? "var(--p-soft)" : "var(--border)",
        display: "flex", alignItems: "center", justifyContent: "center",
        transition: "background 0.13s",
      }}>
        <Icon size={16} color={active ? "var(--p)" : "var(--text-3)"} strokeWidth={1.8} />
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 13.5, fontWeight: 600 }}>{label}</p>
        <p style={{ fontSize: 12, color: active ? "var(--ok)" : "var(--text-3)", marginTop: 2 }}>
          {active ? status : "Disabled"}
        </p>
      </div>
      <button
        role="switch"
        aria-checked={active}
        onClick={onToggle}
        style={{
          width: 40, height: 22, borderRadius: 11, border: "none",
          background: active ? "var(--p)" : "var(--border-strong)",
          cursor: "pointer", position: "relative", flexShrink: 0,
          transition: "background 0.18s",
        }}
      >
        <span style={{
          position: "absolute", top: 3,
          left: active ? 21 : 3,
          width: 16, height: 16, borderRadius: "50%",
          background: "#fff", transition: "left 0.18s",
          boxShadow: "0 1px 3px rgba(0,0,0,0.18)",
        }} />
      </button>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────────────────── */
export default function SettingsPage() {
  const [saved, setSaved] = useState(false);

  /* Profile */
  const [name, setName]   = useState("Admin");
  const [email, setEmail] = useState("admin@crmdigital.io");
  const [timezone, setTZ] = useState("UTC");

  /* Agent / AI */
  const [model, setModel]       = useState("claude-sonnet-4-6");
  const [sla, setSla]           = useState("30");
  const [maxTokens, setTokens]  = useState("1024");
  const [temperature, setTemp]  = useState("0.7");
  const [autoEscalate, setAutoEscalate] = useState(true);
  const [autoResolve, setAutoResolve]   = useState(false);

  /* Notifications */
  const [notifEscalation, setNotifEscalation]   = useState(true);
  const [notifNewTicket, setNotifNewTicket]       = useState(false);
  const [notifDailyReport, setNotifDailyReport]  = useState(true);
  const [notifSentiment, setNotifSentiment]      = useState(true);
  const [notifSound, setNotifSound]              = useState(true);

  /* Channels */
  const [emailEnabled, setEmailEnabled]       = useState(true);
  const [whatsappEnabled, setWhatsappEnabled] = useState(true);
  const [webEnabled, setWebEnabled]           = useState(true);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <Shell>
      <main style={{ padding: "28px 28px 64px", maxWidth: 900 }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Settings</h1>
            <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 3 }}>
              Configure your CRM, AI agent, and notification preferences
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={handleSave}
            style={{ gap: 6, minWidth: 100 }}
          >
            {saved ? <CheckCircle2 size={14} /> : <Save size={14} />}
            {saved ? "Saved!" : "Save changes"}
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>

          {/* ── Profile ── */}
          <Section
            title="Profile"
            description="Your personal details and workspace preferences."
          >
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <Field label="Display name">
                <TextInput value={name} onChange={setName} placeholder="Your name" />
              </Field>
              <Field label="Email address">
                <TextInput value={email} onChange={setEmail} placeholder="you@company.com" type="email" />
              </Field>
            </div>
            <Field label="Timezone">
              <Select
                value={timezone}
                onChange={setTZ}
                options={[
                  { value: "UTC",               label: "UTC" },
                  { value: "America/New_York",   label: "Eastern Time (ET)" },
                  { value: "America/Chicago",    label: "Central Time (CT)" },
                  { value: "America/Los_Angeles",label: "Pacific Time (PT)" },
                  { value: "Europe/London",      label: "London (GMT)" },
                  { value: "Europe/Paris",       label: "Paris (CET)" },
                  { value: "Asia/Dubai",         label: "Dubai (GST)" },
                  { value: "Asia/Kolkata",       label: "India (IST)" },
                  { value: "Asia/Singapore",     label: "Singapore (SGT)" },
                  { value: "Australia/Sydney",   label: "Sydney (AEDT)" },
                ]}
              />
            </Field>
            <Field label="Password">
              <TextInput value="••••••••••" onChange={() => {}} type="password" />
            </Field>
          </Section>

          {/* ── AI Agent ── */}
          <Section
            title="AI Agent"
            description="Configure Agent Alex — the model, response limits, and automation rules."
          >
            <Field label="Model" hint="Sonnet 4.6 offers the best balance of speed and quality for support workflows.">
              <Select
                value={model}
                onChange={setModel}
                options={[
                  { value: "claude-opus-4-6",    label: "Claude Opus 4.6 — Most capable" },
                  { value: "claude-sonnet-4-6",  label: "Claude Sonnet 4.6 — Recommended" },
                  { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5 — Fastest" },
                ]}
              />
            </Field>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              <Field label="Response SLA (seconds)" hint="Target reply time">
                <TextInput value={sla} onChange={setSla} placeholder="30" />
              </Field>
              <Field label="Max tokens" hint="Per response">
                <TextInput value={maxTokens} onChange={setTokens} placeholder="1024" />
              </Field>
              <Field label="Temperature" hint="0 = focused, 1 = creative">
                <TextInput value={temperature} onChange={setTemp} placeholder="0.7" />
              </Field>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 4 }}>
              <Toggle
                checked={autoEscalate}
                onChange={setAutoEscalate}
                label="Auto-escalate critical tickets"
                sub="Tickets with critical sentiment are escalated to human agents automatically"
              />
              <Toggle
                checked={autoResolve}
                onChange={setAutoResolve}
                label="Auto-resolve resolved tickets"
                sub="Mark tickets as resolved after agent confirms customer satisfaction"
              />
            </div>
          </Section>

          {/* ── Notifications ── */}
          <Section
            title="Notifications"
            description="Choose what alerts you receive and how."
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <Toggle
                checked={notifEscalation}
                onChange={setNotifEscalation}
                label="Escalation alerts"
                sub="Notify when a ticket is escalated to human review"
              />
              <Toggle
                checked={notifNewTicket}
                onChange={setNotifNewTicket}
                label="New ticket notifications"
                sub="Alert on every incoming ticket across all channels"
              />
              <Toggle
                checked={notifDailyReport}
                onChange={setNotifDailyReport}
                label="Daily summary report"
                sub="Receive a digest of resolved tickets and sentiment trends each morning"
              />
              <Toggle
                checked={notifSentiment}
                onChange={setNotifSentiment}
                label="Negative sentiment alerts"
                sub="Notify when customer sentiment drops below –0.5"
              />
              <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 4 }}>
                <Toggle
                  checked={notifSound}
                  onChange={setNotifSound}
                  label={notifSound ? "Sound enabled" : "Sound disabled"}
                  sub="Play audio cue for escalation alerts"
                />
              </div>
            </div>
          </Section>

          {/* ── Channel integrations ── */}
          <Section
            title="Channel Integrations"
            description="Enable or disable the support channels Agent Alex monitors."
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <ChannelRow
                icon={Mail}
                label="Email"
                active={emailEnabled}
                onToggle={() => setEmailEnabled(v => !v)}
                status="Receiving via IMAP/SMTP"
              />
              <ChannelRow
                icon={MessageCircle}
                label="WhatsApp"
                active={whatsappEnabled}
                onToggle={() => setWhatsappEnabled(v => !v)}
                status="Connected via WhatsApp Business API"
              />
              <ChannelRow
                icon={Globe}
                label="Web Form"
                active={webEnabled}
                onToggle={() => setWebEnabled(v => !v)}
                status="Receiving from /support"
              />
            </div>
          </Section>

          {/* ── Danger zone ── */}
          <Section
            title="Danger Zone"
            description="Irreversible actions. Be careful."
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "14px 16px", borderRadius: 10,
                border: "1px solid #f0c8c8", background: "var(--danger-soft)",
              }}>
                <div>
                  <p style={{ fontSize: 13.5, fontWeight: 600, color: "var(--danger)" }}>Reset agent memory</p>
                  <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 2 }}>Clear all conversation history and learned context</p>
                </div>
                <button
                  className="btn-secondary"
                  style={{ borderColor: "#d4a0a0", color: "var(--danger)", flexShrink: 0 }}
                  onClick={() => confirm("Reset agent memory? This cannot be undone.") && alert("Agent memory cleared.")}
                >
                  Reset
                </button>
              </div>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "14px 16px", borderRadius: 10,
                border: "1px solid #f0c8c8", background: "var(--danger-soft)",
              }}>
                <div>
                  <p style={{ fontSize: 13.5, fontWeight: 600, color: "var(--danger)" }}>Delete all tickets</p>
                  <p style={{ fontSize: 12, color: "var(--text-3)", marginTop: 2 }}>Permanently remove all ticket data from the database</p>
                </div>
                <button
                  className="btn-secondary"
                  style={{ borderColor: "#d4a0a0", color: "var(--danger)", flexShrink: 0 }}
                  onClick={() => confirm("Delete ALL tickets? This cannot be undone.") && alert("All tickets deleted.")}
                >
                  Delete all
                </button>
              </div>
            </div>
          </Section>

        </div>
      </main>
    </Shell>
  );
}
