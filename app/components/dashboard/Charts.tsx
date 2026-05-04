"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ResponsiveContainer as RechartsContainer } from "recharts";
import { Ticket } from "@/app/lib/types";

export function ChannelChart({ tickets, loading }: { tickets: Ticket[]; loading: boolean }) {
  const data = [
    { name: "Email",    count: tickets.filter(t => t.channel === "email").length,    fill: "#1F5C57" },
    { name: "WhatsApp", count: tickets.filter(t => t.channel === "whatsapp").length, fill: "#2E6A4F" },
    { name: "Web Form", count: tickets.filter(t => t.channel === "web_form").length, fill: "#596A85" },
  ];

  return (
    <div className="card fade-up">
      <div className="card-header">
        <p className="text-[13.5px] font-bold text-[#171717]">Tickets by Channel</p>
      </div>
      <div className="p-5 h-[240px]">
        {loading ? (
          <div className="h-full flex flex-col gap-4 justify-center">
            {[80, 50, 65].map((w, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="skeleton h-4 w-16" />
                <div className="skeleton h-2 flex-1" style={{ width: `${w}%` }} />
                <div className="skeleton h-4 w-8" />
              </div>
            ))}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              barSize={12}
            >
              <XAxis type="number" hide />
              <YAxis 
                dataKey="name" 
                type="category" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 12, fontWeight: 500, fill: "#5F5A52" }}
                width={80}
              />
              <Tooltip 
                cursor={{ fill: '#F6F4EF' }}
                contentStyle={{ 
                  borderRadius: '10px', 
                  border: '1px solid #E6E0D4',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  fontSize: '12px',
                  fontWeight: '600'
                }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
