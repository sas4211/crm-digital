"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { ArrowLeft, MessageSquare, Send, CheckCircle2, Shield, Clock, Hash, RefreshCw } from "lucide-react";
import { cn } from "@/app/lib/utils";

interface FormState {
  name: string; email: string; company: string;
  subject: string; message: string;
  priority: "low" | "medium" | "high";
  category: string;
}

const INITIAL: FormState = {
  name: "", email: "", company: "",
  subject: "", message: "", priority: "medium", category: "general",
};

const MAX_CHARS = 1000;

const CATEGORIES = [
  { value: "general",    label: "General",   icon: "💬" },
  { value: "technical",  label: "Technical", icon: "🔧" },
  { value: "billing",    label: "Billing",   icon: "💳" },
  { value: "bug_report", label: "Bug",       icon: "🐛" },
  { value: "feedback",   label: "Feedback",  icon: "💡" },
];

const PRIORITIES = [
  {
    value: "low",
    label: "Low",
    desc: "Not urgent",
    activeBorder: "border-[#34d399]",
    activeBg: "bg-[#ecfdf5]",
    activeText: "text-[#065f46]",
  },
  {
    value: "medium",
    label: "Medium",
    desc: "Need help soon",
    activeBorder: "border-[#fbbf24]",
    activeBg: "bg-[#fffbeb]",
    activeText: "text-[#92400e]",
  },
  {
    value: "high",
    label: "High",
    desc: "Critical issue",
    activeBorder: "border-[#f87171]",
    activeBg: "bg-[#fff1f2]",
    activeText: "text-[#9f1239]",
  },
];

export default function SupportPage() {
  const [form, setForm]         = useState<FormState>(INITIAL);
  const [loading, setLoading]   = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketId, setTicketId] = useState("");
  const [error, setError]       = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (el) { el.style.height = "auto"; el.style.height = `${el.scrollHeight}px`; }
  }, [form.message]);

  const update = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    let val = e.target.value;
    if (e.target.name === "message") val = val.slice(0, MAX_CHARS);
    setForm(p => ({ ...p, [e.target.name]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      const res = await fetch("/api/webhooks/web-form", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setTicketId(data.ticket_id ?? "TK-" + Math.floor(1000 + Math.random() * 9000));
      setSubmitted(true);
      setForm(INITIAL);
    } catch {
      setError("Could not reach the server. The backend may not be running.");
    } finally {
      setLoading(false);
    }
  };

  const charPct = form.message.length / MAX_CHARS;
  const charColor = charPct >= 1 ? "text-red-500" : charPct >= 0.8 ? "text-amber-500" : "text-[#8A847B]";

  return (
    <div className="min-h-screen bg-[#F6F4EF]">
      {/* Top nav */}
      <header className="bg-white border-b border-[#E6E0D4] sticky top-0 z-30">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#1F5C57] flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-sm">C</span>
            </div>
            <span className="font-extrabold text-[#171717] text-sm uppercase tracking-tight">CRM Digital</span>
          </div>
          <Link href="/" className="flex items-center gap-2 text-[13px] text-[#5F5A52] hover:text-[#171717] transition-colors font-bold">
            <ArrowLeft size={14} />
            Back to dashboard
          </Link>
        </div>
      </header>

      <main className="max-w-[580px] mx-auto px-6 py-12 pb-24">
        {submitted ? (
          <div className="fade-up card shadow-xl shadow-[#1F5C57]/5">
            <div className="h-1 bg-gradient-to-r from-[#1F5C57] to-[#2E6A4F]" />
            <div className="p-10 text-center">
              <div className="relative w-20 h-20 mx-auto mb-6">
                <div className="absolute inset-0 rounded-full bg-[#E8F3EC] animate-ping opacity-50" />
                <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-[#2E6A4F] to-[#34d399] flex items-center justify-center shadow-lg shadow-[#2E6A4F]/20">
                  <CheckCircle2 size={36} className="text-white" strokeWidth={2.5} />
                </div>
              </div>

              <h2 className="text-2xl font-bold text-[#171717] tracking-tight mb-2">Request Received!</h2>
              <p className="text-[14px] text-[#5F5A52] leading-relaxed mb-8 max-w-sm mx-auto">
                Your support request has been logged. Agent Alex will respond within seconds across your preferred channel.
              </p>

              <div className="inline-flex items-center gap-2.5 bg-[#E7F1EF] border border-[#c0d9d6] rounded-xl px-5 py-3 mb-10">
                <div className="p-1.5 bg-[#1F5C57] rounded-lg">
                  <Hash size={12} className="text-white" />
                </div>
                <span className="text-[11px] text-[#174944] font-bold uppercase tracking-widest">Ticket ID</span>
                <span className="text-[16px] font-bold text-[#1F5C57] mono tracking-tight">{ticketId}</span>
              </div>

              <button
                onClick={() => setSubmitted(false)}
                className="btn-primary w-full justify-center py-3.5 shadow-lg shadow-[#1F5C57]/20"
              >
                Submit Another Request
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="fade-up mb-8">
              <h1 className="text-3xl font-bold text-[#171717] tracking-tighter mb-2">Support Request</h1>
              <div className="flex items-center gap-2 text-[14px] text-[#5F5A52] font-medium">
                <span className="flex items-center gap-1.5 bg-[#E8F3EC] px-2 py-0.5 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#2E6A4F] animate-pulse" />
                  <span className="text-[11px] font-bold text-[#2E6A4F] uppercase tracking-wider">Agent Alex online</span>
                </span>
                <span>· responds in seconds</span>
              </div>
            </div>

            <div className="fade-up card shadow-xl shadow-[#1F5C57]/5">
              <div className="bg-[#1F5C57] p-6 px-8 flex items-center gap-4">
                <div className="w-11 h-11 rounded-xl bg-white/15 backdrop-blur-md flex items-center justify-center border border-white/20">
                  <MessageSquare size={22} className="text-white" />
                </div>
                <div>
                  <p className="text-white font-bold text-lg leading-tight">Contact Support</p>
                  <p className="text-white/60 text-[12px] font-medium tracking-wide">AI-powered · Response within seconds</p>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="p-8 space-y-6">
                {error && (
                  <div className="flex items-start gap-3 bg-[#F8E6E6] border border-[#f0c8c8] rounded-xl p-4 animate-in slide-in-from-top-1">
                    <Shield size={16} className="text-[#A04646] shrink-0 mt-0.5" />
                    <p className="text-[13px] text-[#A04646] font-medium leading-relaxed">{error}</p>
                  </div>
                )}

                <div className="space-y-4">
                  <p className="text-[10px] font-bold text-[#8A847B] uppercase tracking-widest px-1">Contact Info</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FieldGroup label="Name" required>
                      <input name="name" value={form.name} onChange={update} required placeholder="Jane Smith" className="support-input" />
                    </FieldGroup>
                    <FieldGroup label="Email" required>
                      <input name="email" type="email" value={form.email} onChange={update} required placeholder="jane@company.com" className="support-input" />
                    </FieldGroup>
                  </div>
                  <FieldGroup label="Company">
                    <input name="company" value={form.company} onChange={update} placeholder="Acme Corp" className="support-input" />
                  </FieldGroup>
                </div>

                <div className="h-px bg-[#E6E0D4]" />

                <div className="space-y-4">
                  <p className="text-[10px] font-bold text-[#8A847B] uppercase tracking-widest px-1">Issue Details</p>
                  <FieldGroup label="Subject" required>
                    <input name="subject" value={form.subject} onChange={update} required placeholder="Briefly describe the issue" className="support-input" />
                  </FieldGroup>

                  <FieldGroup label="Category">
                    <div className="flex flex-wrap gap-2">
                      {CATEGORIES.map(cat => (
                        <button
                          key={cat.value} type="button"
                          onClick={() => setForm(p => ({ ...p, category: cat.value }))}
                          className={cn(
                            "flex items-center gap-2 px-3 py-1.5 rounded-full text-[13px] font-bold border transition-all",
                            form.category === cat.value 
                              ? "bg-[#E7F1EF] border-[#1F5C57] text-[#174944] shadow-sm" 
                              : "bg-white border-[#E6E0D4] text-[#5F5A52] hover:border-[#D7D0C2]"
                          )}
                        >
                          <span className="text-[14px]">{cat.icon}</span>
                          {cat.label}
                        </button>
                      ))}
                    </div>
                  </FieldGroup>

                  <FieldGroup label="Priority">
                    <div className="grid grid-cols-3 gap-3">
                      {PRIORITIES.map(opt => {
                        const active = form.priority === opt.value;
                        return (
                          <button
                            key={opt.value} type="button"
                            onClick={() => setForm(p => ({ ...p, priority: opt.value as any }))}
                            className={cn(
                              "relative flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all group",
                              active ? cn("bg-white shadow-md", opt.activeBorder) : "bg-white border-[#E6E0D4] hover:border-[#D7D0C2]"
                            )}
                          >
                            <span className={cn("text-[13px] font-bold", active ? opt.activeText : "text-[#5F5A52]")}>{opt.label}</span>
                            <span className={cn("text-[10px] text-center leading-tight font-medium", active ? "text-[#5F5A52]" : "text-[#8A847B]")}>{opt.desc}</span>
                            {active && <span className={cn("absolute top-2 right-2 w-1.5 h-1.5 rounded-full ring-2 ring-white", opt.activeBorder.replace("border-", "bg-"))} />}
                          </button>
                        );
                      })}
                    </div>
                  </FieldGroup>

                  <FieldGroup label="Message" required>
                    <textarea
                      ref={textareaRef}
                      name="message" value={form.message} onChange={update} required
                      placeholder="Describe your issue in detail..."
                      rows={4}
                      className="support-input resize-none overflow-hidden min-h-[120px]"
                    />
                    <div className="flex justify-between items-center mt-2 px-1">
                      <p className="text-[11px] text-[#8A847B] font-medium flex items-center gap-1.5">
                        <Clock size={10} />
                        Detailed descriptions get faster solutions
                      </p>
                      <span className={cn("text-[11px] font-bold tabular-nums transition-colors", charColor)}>
                        {form.message.length}/{MAX_CHARS}
                      </span>
                    </div>
                  </FieldGroup>
                </div>

                <button
                  type="submit" disabled={loading}
                  className={cn(
                    "btn-primary w-full justify-center py-4 text-sm tracking-wide shadow-lg transition-all active:scale-[0.98]",
                    loading ? "opacity-70 cursor-not-allowed shadow-none" : "shadow-[#1F5C57]/20"
                  )}
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw size={16} className="animate-spin" />
                      Sending to Alex...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      Send Request
                      <Send size={16} />
                    </span>
                  )}
                </button>
              </form>
            </div>
          </>
        )}
      </main>

      <style jsx>{`
        .support-input {
          width: 100%;
          background: #F6F4EF;
          border: 1.5px solid #E6E0D4;
          border-radius: 12px;
          padding: 10px 14px;
          color: #171717;
          font-family: inherit;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.15s;
          outline: none;
        }
        .support-input:focus {
          border-color: #1F5C57;
          background: white;
          box-shadow: 0 0 0 4px rgba(31, 92, 87, 0.08);
        }
        .support-input::placeholder {
          color: #8A847B;
        }
      `}</style>
    </div>
  );
}

function FieldGroup({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-[11px] font-bold text-[#8A847B] uppercase tracking-[0.05em] ml-1">
        {label}{required && <span className="text-[#1F5C57] ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}
