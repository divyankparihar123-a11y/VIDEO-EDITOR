"use client";

import type { StylePreset } from "@/lib/types";

interface StylePresetPickerProps {
  value: StylePreset;
  onChange: (value: StylePreset) => void;
}

const PRESETS: { id: StylePreset; label: string; emoji: string; desc: string; accent: string }[] = [
  {
    id: "cinematic",
    label: "Cinematic",
    emoji: "🎬",
    desc: "Dark, moody colour grade with slow xfade transitions",
    accent: "hsl(220, 80%, 60%)",
  },
  {
    id: "energetic",
    label: "Energetic",
    emoji: "⚡",
    desc: "High saturation, fast cuts, dynamic wipe transitions",
    accent: "hsl(38, 100%, 55%)",
  },
  {
    id: "luxury",
    label: "Luxury",
    emoji: "💎",
    desc: "Rich contrast, deep vignette, slow silky transitions",
    accent: "hsl(38, 75%, 60%)",
  },
  {
    id: "vlog",
    label: "Vlog",
    emoji: "📱",
    desc: "Warm tones, natural pacing, casual feel",
    accent: "hsl(15, 80%, 60%)",
  },
];

export default function StylePresetPicker({ value, onChange }: StylePresetPickerProps) {
  return (
    <div>
      <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 14 }}>
        Style Preset
      </label>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
        {PRESETS.map((preset) => {
          const selected = value === preset.id;
          return (
            <button
              key={preset.id}
              id={`preset-${preset.id}`}
              type="button"
              onClick={() => onChange(preset.id)}
              style={{
                padding: "16px",
                borderRadius: 12,
                border: selected
                  ? `1px solid ${preset.accent}`
                  : "1px solid var(--border-subtle)",
                background: selected
                  ? `${preset.accent}18`
                  : "hsl(224, 20%, 10%)",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.2s var(--ease-spring)",
                transform: selected ? "scale(1.02)" : "scale(1)",
                boxShadow: selected
                  ? `0 0 20px ${preset.accent}30`
                  : "none",
              }}
              aria-pressed={selected}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <span style={{ fontSize: 20 }}>{preset.emoji}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: selected ? preset.accent : "var(--text-primary)" }}>
                  {preset.label}
                </span>
                {selected && (
                  <span style={{
                    marginLeft: "auto",
                    width: 18, height: 18,
                    borderRadius: "50%",
                    background: preset.accent,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11, color: "#000", fontWeight: 800
                  }}>✓</span>
                )}
              </div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0, lineHeight: 1.4 }}>
                {preset.desc}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
