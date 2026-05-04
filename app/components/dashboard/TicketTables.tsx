"use client";

import { useState } from "react";
import { MoreHorizontal, CheckCircle2 } from "lucide-react";
import { Ticket, STATUS_CONFIG, PRIORITY_CONFIG, CHANNEL_CONFIG } from "@/app/lib/types";
import { timeAgo, sentimentToLabel, cn } from "@/app/lib/utils";

interface TableProps {
  tickets: Ticket[];
  loading: boolean;
  onTicketClick: (ticket: Ticket) => void;
}

export function AttentionTable({ tickets, loading, onTicketClick }: TableProps) {
  const attention = tickets
    .filter(t => t.status === "escalated" || t.priority === "critical" || t.priority === "high")
    .sort((a, b) => {
      const rank = { escalated: 0, critical: 1, high: 2 } as Record<string, number>;
      return (rank[a.status] ?? rank[a.priority] ?? 3) - (rank[b.status] ?? rank[b.priority] ?? 3);
    })
    .slice(0, 8);

  return (
    <div className="card fade-up">
      <div className="card-header">
        <div>
          <p className="text-[13.5px] font-bold text-[#171717]">Tickets Needing Attention</p>
          {!loading && attention.length > 0 && (
            <p className="text-[12px] text-[#8A847B] mt-0.5">
              {attention.filter(t => t.status === "escalated").length} escalated · {attention.filter(t => t.priority === "critical").length} critical
            </p>
          )}
        </div>
        <button className="btn-ghost p-1">
          <MoreHorizontal size={15} />
        </button>
      </div>

      <div className="overflow-x-auto">
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
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j}><div className="skeleton h-3.5" style={{ width: j === 0 ? "180px" : "60px" }} /></td>
                  ))}
                </tr>
              ))
            ) : attention.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-[#8A847B]">
                  <CheckCircle2 size={20} className="mx-auto mb-2 text-[#2E6A4F]" />
                  No tickets need immediate attention
                </td>
              </tr>
            ) : (
              attention.map((t) => (
                <TicketRow key={t.id} ticket={t} onClick={() => onTicketClick(t)} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AllTickets({ tickets, loading, onTicketClick }: TableProps) {
  const [filter, setFilter] = useState<string>("all");
  const filtered = filter === "all" ? tickets : tickets.filter(t => t.status === filter);

  const filters = [
    { key: "all",        label: `All (${tickets.length})` },
    { key: "open",       label: `Open (${tickets.filter(t => t.status === "open").length})` },
    { key: "in_progress",label: `Active (${tickets.filter(t => t.status === "in_progress").length})` },
    { key: "escalated",  label: `Escalated (${tickets.filter(t => t.status === "escalated").length})` },
    { key: "resolved",   label: `Resolved (${tickets.filter(t => t.status === "resolved").length})` },
  ];

  return (
    <div className="card fade-up">
      <div className="card-header flex-wrap gap-3">
        <p className="text-[13.5px] font-bold text-[#171717]">All Tickets</p>
        <div className="flex gap-1.5 flex-wrap">
          {filters.map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                "px-2.5 py-1 rounded-lg border text-[12px] font-bold transition-all",
                filter === f.key 
                  ? "bg-[#E7F1EF] text-[#174944] border-[#E7F1EF]" 
                  : "bg-transparent text-[#5F5A52] border-[#E6E0D4] hover:border-[#D7D0C2]"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto">
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
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j}><div className="skeleton h-3.5" style={{ width: j === 0 ? "200px" : "70px" }} /></td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-[#8A847B]">
                  No tickets match this filter.
                </td>
              </tr>
            ) : (
              filtered.map((t) => (
                <TicketRow key={t.id} ticket={t} onClick={() => onTicketClick(t)} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TicketRow({ ticket, onClick }: { ticket: Ticket; onClick: () => void }) {
  const st = STATUS_CONFIG[ticket.status];
  const pr = PRIORITY_CONFIG[ticket.priority];
  const ch = CHANNEL_CONFIG[ticket.channel];
  const sm = sentimentToLabel(ticket.sentiment);

  return (
    <tr 
      onClick={onClick} 
      className="cursor-pointer group hover:bg-[#F6F4EF]/50"
    >
      <td className="max-w-[280px]">
        <p className="font-bold text-[#171717] truncate group-hover:text-[#1F5C57] transition-colors">
          {ticket.subject}
        </p>
        {ticket.customer_id && (
          <p className="text-[11px] text-[#8A847B] mt-0.5 mono">
            {ticket.customer_id.slice(0, 8)}
          </p>
        )}
      </td>
      <td>
        <span className="flex items-center gap-1.5 text-[#5F5A52] text-[13px] font-medium">
          <ch.Icon size={13} strokeWidth={2} />
          {ch.label}
        </span>
      </td>
      <td><span className={cn("chip", st.cls)}>{st.label}</span></td>
      <td>
        <span className={cn("text-[13px] font-bold", pr.tailwind)}>{pr.label}</span>
      </td>
      <td><span className={cn("chip", sm.cls)}>{sm.label}</span></td>
      <td className="text-[#8A847B] text-[13px] font-medium whitespace-nowrap">{timeAgo(ticket.created_at)}</td>
    </tr>
  );
}
