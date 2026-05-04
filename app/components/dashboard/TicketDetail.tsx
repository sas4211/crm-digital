"use client";

import { X, Mail, MessageCircle, Globe, Clock, User, MessageSquare, ShieldAlert, CheckCircle2 } from "lucide-react";
import { Ticket, STATUS_CONFIG, PRIORITY_CONFIG, CHANNEL_CONFIG } from "@/app/lib/types";
import { timeAgo, sentimentToLabel, cn } from "@/app/lib/utils";

interface TicketDetailProps {
  ticket: Ticket | null;
  onClose: () => void;
}

export function TicketDetail({ ticket, onClose }: TicketDetailProps) {
  if (!ticket) return null;

  const st = STATUS_CONFIG[ticket.status];
  const pr = PRIORITY_CONFIG[ticket.priority];
  const ch = CHANNEL_CONFIG[ticket.channel];
  const sm = sentimentToLabel(ticket.sentiment);

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/20 backdrop-blur-[2px] z-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-[#FCFBF8] border-l border-[#E6E0D4] shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-300 ease-out">
        {/* Header */}
        <div className="px-6 py-5 border-bottom flex items-center justify-between bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-lg font-bold text-[#171717] tracking-tight line-clamp-1">{ticket.subject}</h2>
            <p className="text-xs text-[#8A847B] mono mt-0.5">{ticket.id}</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-[#F6F4EF] rounded-full transition-colors text-[#5F5A52]"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* Status Bar */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="p-3 bg-white rounded-xl border border-[#E6E0D4]">
              <p className="text-[10px] font-bold text-[#8A847B] uppercase mb-1">Status</p>
              <span className={cn("chip", st.cls)}>{st.label}</span>
            </div>
            <div className="p-3 bg-white rounded-xl border border-[#E6E0D4]">
              <p className="text-[10px] font-bold text-[#8A847B] uppercase mb-1">Priority</p>
              <span className="text-sm font-bold" style={{ color: pr.color }}>{pr.label}</span>
            </div>
            <div className="p-3 bg-white rounded-xl border border-[#E6E0D4]">
              <p className="text-[10px] font-bold text-[#8A847B] uppercase mb-1">Channel</p>
              <div className="flex items-center gap-2 text-sm font-medium text-[#5F5A52]">
                <ch.Icon size={14} />
                {ch.label}
              </div>
            </div>
            <div className="p-3 bg-white rounded-xl border border-[#E6E0D4]">
              <p className="text-[10px] font-bold text-[#8A847B] uppercase mb-1">Sentiment</p>
              <span className={cn("chip", sm.cls)}>{sm.label}</span>
            </div>
          </div>

          {/* Details */}
          <section className="mb-8">
            <h3 className="text-sm font-bold text-[#171717] uppercase tracking-wider mb-4 border-l-2 border-[#1F5C57] pl-3">Details</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <User size={16} className="text-[#8A847B] mt-1" />
                <div>
                  <p className="text-xs font-bold text-[#8A847B] uppercase">Customer</p>
                  <p className="text-sm font-medium text-[#171717]">{ticket.customer_id || "Anonymous"}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Clock size={16} className="text-[#8A847B] mt-1" />
                <div>
                  <p className="text-xs font-bold text-[#8A847B] uppercase">Opened</p>
                  <p className="text-sm font-medium text-[#171717]">{new Date(ticket.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="mt-6 p-4 bg-[#F6F4EF] rounded-xl text-[#5F5A52] text-sm leading-relaxed italic border-l-4 border-[#D7D0C2]">
                {ticket.description || "No description provided."}
              </div>
            </div>
          </section>

          {/* Activity Mockup */}
          <section>
            <h3 className="text-sm font-bold text-[#171717] uppercase tracking-wider mb-4 border-l-2 border-[#1F5C57] pl-3">Activity</h3>
            <div className="space-y-6 relative before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-[2px] before:bg-[#E6E0D4]">
              <div className="flex gap-4 relative">
                <div className="w-4 h-4 rounded-full bg-[#1F5C57] border-4 border-white z-10" />
                <div>
                  <p className="text-sm font-bold text-[#171717]">Ticket Created</p>
                  <p className="text-xs text-[#8A847B]">{timeAgo(ticket.created_at)}</p>
                </div>
              </div>
              {ticket.status === "escalated" && (
                <div className="flex gap-4 relative">
                  <div className="w-4 h-4 rounded-full bg-[#A04646] border-4 border-white z-10" />
                  <div>
                    <p className="text-sm font-bold text-[#A04646]">Auto-Escalated by AI</p>
                    <p className="text-xs text-[#8A847B]">Negative sentiment and high priority detected</p>
                  </div>
                </div>
              )}
              <div className="flex gap-4 relative">
                <div className="w-4 h-4 rounded-full bg-[#E6E0D4] border-4 border-white z-10" />
                <div>
                  <p className="text-sm font-medium text-[#5F5A52]">Agent Alex assigned</p>
                  <p className="text-xs text-[#8A847B]">System</p>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#E6E0D4] bg-white flex gap-3">
          <button className="btn-primary flex-1 justify-center py-3">
            <MessageSquare size={16} />
            Reply to Customer
          </button>
          <button className="btn-secondary px-4">
            {ticket.status === "resolved" ? "Reopen" : "Resolve"}
          </button>
        </div>
      </div>
    </>
  );
}
