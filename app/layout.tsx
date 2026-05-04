import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CRM Digital — Command Center",
  description: "AI-powered customer support operations. Monitor tickets, escalations, and agent performance across email, WhatsApp, and web.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
