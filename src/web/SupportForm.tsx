"use client";

/**
 * SupportForm — embeddable web support form.
 * Posts to FastAPI /webhooks/web-form and displays the agent's reply inline.
 *
 * Usage:
 *   import SupportForm from "@/components/SupportForm";
 *   <SupportForm apiBase="https://api.yourdomain.com" />
 */

import { useState, useRef, useEffect } from "react";

interface FormState {
  name: string;
  email: string;
  company: string;
  subject: string;
  message: string;
  priority: "low" | "medium" | "high";
}

interface AgentResponse {
  ticket_id: string;
  reply: string;
  escalated: boolean;
}

const INITIAL: FormState = {
  name: "",
  email: "",
  company: "",
  subject: "",
  message: "",
  priority: "medium",
};

const MAX_CHARS = 1000;

const PRIORITY_OPTIONS = [
  {
    value: "low" as const,
    label: "Low",
    desc: "Not urgent",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    ring: "ring-emerald-400",
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-400",
    badge: "bg-emerald-100 text-emerald-700",
  },
  {
    value: "medium" as const,
    label: "Medium",
    desc: "Need help soon",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    ring: "ring-amber-400",
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-400",
    badge: "bg-amber-100 text-amber-700",
  },
  {
    value: "high" as const,
    label: "High",
    desc: "Critical issue",
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    ring: "ring-rose-400",
    bg: "bg-rose-50",
    text: "text-rose-700",
    border: "border-rose-400",
    badge: "bg-rose-100 text-rose-700",
  },
];

function InputField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="group">
      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
        {label}
        {required && <span className="text-indigo-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 " +
  "transition-all duration-200 outline-none " +
  "focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 focus:bg-white " +
  "hover:border-slate-300";

export default function SupportForm({ apiBase = "" }: { apiBase?: string }) {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState("");
  const [focused, setFocused] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [form.message]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const val =
      e.target.name === "message"
        ? e.target.value.slice(0, MAX_CHARS)
        : e.target.value;
    setForm((prev) => ({ ...prev, [e.target.name]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResponse(null);

    try {
      const res = await fetch(`${apiBase}/webhooks/web-form`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `Server error ${res.status}`);
      }
      const data: AgentResponse = await res.json();
      setResponse(data);
      setForm(INITIAL);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const charPct = form.message.length / MAX_CHARS;
  const charColor =
    charPct >= 1
      ? "text-rose-500"
      : charPct >= 0.8
      ? "text-amber-500"
      : "text-slate-400";

  const activePriority = PRIORITY_OPTIONS.find((p) => p.value === form.priority)!;

  // ── Success ──────────────────────────────────────────────────────────────────
  if (response) {
    return (
      <div className="w-full max-w-lg mx-auto">
        <div className="rounded-2xl overflow-hidden shadow-xl shadow-slate-200/60 border border-slate-100">
          {/* Header */}
          <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-900 px-6 py-5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <span className="text-white font-semibold text-sm tracking-wide">CRM Support</span>
          </div>

          {/* Body */}
          <div className="bg-white px-6 py-8 text-center space-y-5">
            {/* Animated ring */}
            <div className="relative w-20 h-20 mx-auto">
              <div className="absolute inset-0 rounded-full bg-emerald-100 animate-ping opacity-30" />
              <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-200">
                <svg className="w-9 h-9 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>

            <div>
              <h2 className="text-xl font-bold text-slate-900">
                {response.escalated ? "Ticket Created" : "Message Received!"}
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {response.escalated
                  ? "A human agent will follow up with you shortly."
                  : "Our AI agent Alex has reviewed your request."}
              </p>
            </div>

            {/* Reply */}
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-left border border-slate-100">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                Agent Reply
              </p>
              <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                {response.reply}
              </p>
            </div>

            {/* Ticket ID */}
            <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-2">
              <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
              <span className="text-xs text-indigo-400 font-medium">Ticket</span>
              <span className="text-xs font-mono font-bold text-indigo-700">{response.ticket_id}</span>
            </div>

            <button
              onClick={() => setResponse(null)}
              className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:from-indigo-500 hover:to-violet-500 transition-all duration-200 shadow-md shadow-indigo-200 hover:shadow-lg hover:shadow-indigo-300 active:scale-[0.98]"
            >
              Submit Another Request
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Form ─────────────────────────────────────────────────────────────────────
  return (
    <div className="w-full max-w-lg mx-auto">
      <div className="rounded-2xl overflow-hidden shadow-xl shadow-slate-200/60 border border-slate-100">

        {/* Header */}
        <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-900 px-6 py-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-white font-bold text-base leading-tight">Contact Support</h2>
              <p className="text-indigo-300 text-xs">AI agent Alex replies within seconds, 24/7</p>
            </div>
          </div>
          {/* Live indicator */}
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-300 font-medium">Online now</span>
          </div>
        </div>

        {/* Form body */}
        <form onSubmit={handleSubmit} className="bg-white px-6 py-6 space-y-5">

          {/* Error */}
          {error && (
            <div className="flex items-start gap-3 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
              <svg className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-rose-700">{error}</p>
            </div>
          )}

          {/* Section: Contact Info */}
          <div className="space-y-4">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
              Contact Info
            </p>

            {/* Name + Email row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <InputField label="Name" required>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </span>
                  <input
                    name="name" value={form.name} onChange={handleChange} required
                    placeholder="Jane Smith"
                    onFocus={() => setFocused("name")}
                    onBlur={() => setFocused(null)}
                    className={`${inputCls} pl-9`}
                  />
                </div>
              </InputField>

              <InputField label="Email" required>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </span>
                  <input
                    name="email" type="email" value={form.email} onChange={handleChange} required
                    placeholder="jane@company.com"
                    onFocus={() => setFocused("email")}
                    onBlur={() => setFocused(null)}
                    className={`${inputCls} pl-9`}
                  />
                </div>
              </InputField>
            </div>

            {/* Company */}
            <InputField label="Company">
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </span>
                <input
                  name="company" value={form.company} onChange={handleChange}
                  placeholder="Acme Corp"
                  className={`${inputCls} pl-9`}
                />
              </div>
            </InputField>
          </div>

          {/* Divider */}
          <div className="border-t border-slate-100" />

          {/* Section: Issue Details */}
          <div className="space-y-4">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
              Issue Details
            </p>

            {/* Subject */}
            <InputField label="Subject" required>
              <input
                name="subject" value={form.subject} onChange={handleChange} required
                placeholder="Can't log in to my account"
                className={inputCls}
              />
            </InputField>

            {/* Priority — visual cards */}
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Priority
              </p>
              <div className="grid grid-cols-3 gap-2">
                {PRIORITY_OPTIONS.map((opt) => {
                  const active = form.priority === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setForm((p) => ({ ...p, priority: opt.value }))}
                      className={`
                        relative flex flex-col items-center gap-1 rounded-xl border-2 px-2 py-3
                        transition-all duration-200 cursor-pointer select-none
                        ${active
                          ? `${opt.border} ${opt.bg} shadow-sm`
                          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"}
                      `}
                    >
                      <span className={active ? opt.text : "text-slate-400"}>
                        {opt.icon}
                      </span>
                      <span className={`text-xs font-bold ${active ? opt.text : "text-slate-600"}`}>
                        {opt.label}
                      </span>
                      <span className={`text-[10px] text-center leading-tight ${active ? opt.text : "text-slate-400"}`}>
                        {opt.desc}
                      </span>
                      {active && (
                        <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-current" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Message */}
            <InputField label="Message" required>
              <div className="relative">
                <textarea
                  ref={textareaRef}
                  name="message" value={form.message} onChange={handleChange} required
                  placeholder="Describe your issue in detail…"
                  rows={4}
                  className={`${inputCls} resize-none min-h-[100px] leading-relaxed`}
                  style={{ overflow: "hidden" }}
                />
                <div className="flex items-center justify-between mt-1.5 px-0.5">
                  <span className="text-[11px] text-slate-400">Be as specific as possible</span>
                  <span className={`text-[11px] font-medium tabular-nums transition-colors ${charColor}`}>
                    {form.message.length}/{MAX_CHARS}
                  </span>
                </div>
              </div>
            </InputField>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className={`
              w-full rounded-xl px-4 py-3 text-sm font-bold text-white
              transition-all duration-200 relative overflow-hidden
              ${loading
                ? "bg-indigo-400 cursor-not-allowed"
                : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-md shadow-indigo-200 hover:shadow-lg hover:shadow-indigo-300 active:scale-[0.98]"}
            `}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Sending to Alex…
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                Send Message
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            )}
          </button>

          {/* Footer note */}
          <p className="text-center text-[11px] text-slate-400">
            Secured by CRM Digital · AI-powered response within seconds
          </p>
        </form>
      </div>
    </div>
  );
}
