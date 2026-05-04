export function timeAgo(iso: string) {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (d < 1)  return "just now";
  if (d < 60) return `${d}m ago`;
  const h = Math.floor(d / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function sentimentToLabel(s: number | null) {
  if (s === null) return { label: "—", cls: "chip-neutral" };
  if (s >= 0.4)  return { label: "Positive", cls: "chip-ok"      };
  if (s >= -0.1) return { label: "Neutral",  cls: "chip-neutral" };
  if (s >= -0.5) return { label: "Negative", cls: "chip-warn"    };
  return               { label: "Critical",  cls: "chip-danger"  };
}

export function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}
