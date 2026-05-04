"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/app/lib/utils";

interface KPICardProps {
  label: string;
  value: string | number | undefined;
  sub?: string;
  accentColor?: string;
  icon: LucideIcon;
  loading: boolean;
  className?: string;
}

export function KPICard({
  label, value, sub, accentColor, icon: Icon, loading, className
}: KPICardProps) {
  return (
    <div className={cn("card fade-up p-5 flex flex-col justify-between h-full", className)}>
      <div className="flex items-start justify-between mb-3">
        <p className="text-[11px] font-bold text-[#8A847B] uppercase tracking-wider">
          {label}
        </p>
        <div className="p-1.5 bg-[#F6F4EF] rounded-lg">
          <Icon size={14} className="text-[#5F5A52]" strokeWidth={2} />
        </div>
      </div>
      
      <div>
        {loading ? (
          <div className="skeleton h-8 w-20 mb-1" />
        ) : (
          <p 
            className="text-3xl font-bold tracking-tight text-[#171717]"
            style={accentColor ? { color: accentColor } : {}}
          >
            {value ?? "—"}
          </p>
        )}
        
        {sub && !loading && (
          <p className="text-[12px] text-[#8A847B] mt-1.5 font-medium">{sub}</p>
        )}
      </div>
    </div>
  );
}

import { Ticket, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

export function KPIGrid({ 
  report, 
  openCount, 
  escalatedCount, 
  totalCount, 
  loading 
}: { 
  report: any; 
  openCount: number; 
  escalatedCount: number; 
  totalCount: number;
  loading: boolean;
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <KPICard 
        label="Total Today"    
        value={report?.total_tickets}     
        loading={loading} 
        icon={Ticket}        
      />
      <KPICard 
        label="Open / Active"  
        value={loading ? undefined : openCount}
        sub={`${totalCount} total loaded`}                   
        loading={loading} 
        icon={Clock}         
      />
      <KPICard 
        label="Escalated"      
        value={report?.escalated ?? (loading ? undefined : escalatedCount)}
        accentColor={escalatedCount > 0 ? "var(--danger)" : undefined}
        loading={loading} 
        icon={AlertTriangle} 
      />
      <KPICard 
        label="Resolved Today" 
        value={report?.resolved}          
        loading={loading} 
        icon={CheckCircle2}  
        accentColor="var(--ok)" 
      />
    </div>
  );
}
