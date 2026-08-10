"use client";

import type { AspectRatio } from "@/lib/types";

interface AspectRatioPickerProps {
  value: AspectRatio;
  onChange: (value: AspectRatio) => void;
}

const OPTIONS: { id: AspectRatio; label: string; icon: string; desc: string; w: number; h: number }[] = [
  { id: "9:16", label: "9:16", icon: "📱", desc: "Stories / Reels", w: 18, h: 32 },
  { id: "16:9", label: "16:9", icon: "🖥️", desc: "YouTube / Landscape", w: 32, h: 18 },
  { id: "1:1",  label: "1:1",  icon: "⬜", desc: "Instagram / Square", w: 24, h: 24 },
];

export default function AspectRatioPicker({ value, onChange }: AspectRatioPickerProps) {
  return (
    <div>
      <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 14 }}>
        Aspect Ratio
      </label>
      <div style={{ display: "flex", gap: 10 }}>
        {OPTIONS.map((opt) => {
          const selected = value === opt.id;
          return (
            <button
              key={opt.id}
              id={`aspect-${opt.id.replace(":", "x")}`}
              type="button"
              onClick={() => onChange(opt.id)}
              style={{
                flex: 1,
                padding: "14px 10px",
                borderRadius: 12,
                border: selected
                  ? "1px solid var(--brand-cyan)"
                  : "1px solid var(--border-subtle)",
                background: selected
                  ? "hsl(192, 100%, 50%, 0.08)"
                  : "hsl(224, 20%, 10%)",
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 10,
                transition: "all 0.2s var(--ease-spring)",
                transform: selected ? "scale(1.03)" : "scale(1)",
                boxShadow: selected ? "0 0 20px hsl(192,100%,50%,0.2)" : "none",
              }}
              aria-pressed={selected}
            >
              {/* Visual aspect ratio box */}
              <div style={{
                width: opt.w, height: opt.h,
                border: `2px solid ${selected ? "var(--brand-cyan)" : "hsl(224, 20%, 35%)"}`,
                borderRadius: 3,
                background: selected ? "hsl(192, 100%, 50%, 0.1)" : "transparent",
                transition: "all 0.2s ease",
              }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: selected ? "var(--brand-cyan)" : "var(--text-primary)" }}>
                  {opt.label}
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                  {opt.desc}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
