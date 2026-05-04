import { Mail, MessageCircle, Globe, LucideIcon } from "lucide-react";

export interface Ticket {
  id: string;
  subject: string;
  status: "open" | "in_progress" | "waiting_customer" | "escalated" | "resolved" | "closed";
  channel: "email" | "whatsapp" | "web_form";
  priority: "low" | "medium" | "high" | "critical";
  sentiment: number | null;
  created_at: string;
  customer_id?: string;
  description?: string;
}

export interface DailyReport {
  total_tickets: number;
  resolved: number;
  escalated: number;
  avg_sentiment: number | null;
  top_issues: { keyword: string; count: number }[];
  summary?: string;
  summary_text?: string;
}

export interface Health {
  agent: string;
  model: string;
  status?: string;
}

export const STATUS_CONFIG: Record<Ticket["status"], { label: string; cls: string }> = {
  open:             { label: "Open",          cls: "chip-warn"    },
  in_progress:      { label: "In Progress",   cls: "chip-info"    },
  waiting_customer: { label: "Waiting",       cls: "chip-neutral" },
  escalated:        { label: "Escalated",     cls: "chip-danger"  },
  resolved:         { label: "Resolved",      cls: "chip-ok"      },
  closed:           { label: "Closed",        cls: "chip-neutral" },
};

export const PRIORITY_CONFIG: Record<Ticket["priority"], { label: string; color: string; tailwind: string }> = {
  low:      { label: "Low",      color: "var(--text-3)", tailwind: "text-neutral-500" },
  medium:   { label: "Medium",   color: "var(--warn)",    tailwind: "text-amber-600"   },
  high:     { label: "High",     color: "var(--danger)",  tailwind: "text-red-600"     },
  critical: { label: "Critical", color: "var(--danger)",  tailwind: "text-red-700"     },
};

export const CHANNEL_CONFIG: Record<Ticket["channel"], { label: string; Icon: LucideIcon }> = {
  email:    { label: "Email",    Icon: Mail           },
  whatsapp: { label: "WhatsApp", Icon: MessageCircle  },
  web_form: { label: "Web",      Icon: Globe          },
};
