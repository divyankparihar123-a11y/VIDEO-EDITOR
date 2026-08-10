"use client";

interface DurationSliderProps {
  value: number;
  onChange: (value: number) => void;
}

const PRESETS = [15, 30, 60, 90, 120];

function formatDuration(sec: number): string {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return s === 0 ? `${m}m` : `${m}m ${s}s`;
}

export default function DurationSlider({ value, onChange }: DurationSliderProps) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <label htmlFor="duration-slider" style={{ fontSize: 14, fontWeight: 600, color: "var(--text-secondary)" }}>
          Target Duration
        </label>
        <div style={{
          padding: "4px 14px",
          background: "hsl(192, 100%, 50%, 0.1)",
          border: "1px solid hsl(192, 100%, 50%, 0.25)",
          borderRadius: 99,
          fontSize: 15,
          fontWeight: 700,
          color: "var(--brand-cyan)",
          fontFamily: "JetBrains Mono, monospace",
          minWidth: 60,
          textAlign: "center",
        }}>
          {formatDuration(value)}
        </div>
      </div>

      <input
        id="duration-slider"
        type="range"
        min={10}
        max={180}
        step={5}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: "100%", marginBottom: 16 }}
      />

      {/* Quick presets */}
      <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
        {PRESETS.map((preset) => (
          <button
            key={preset}
            id={`duration-preset-${preset}`}
            type="button"
            onClick={() => onChange(preset)}
            style={{
              flex: 1,
              padding: "6px 0",
              borderRadius: 8,
              border: value === preset
                ? "1px solid var(--brand-cyan)"
                : "1px solid var(--border-subtle)",
              background: value === preset
                ? "hsl(192, 100%, 50%, 0.1)"
                : "hsl(224, 20%, 12%)",
              color: value === preset ? "var(--brand-cyan)" : "var(--text-muted)",
              cursor: "pointer",
              fontSize: 12,
              fontWeight: 600,
              transition: "all 0.2s ease",
            }}
          >
            {formatDuration(preset)}
          </button>
        ))}
      </div>
    </div>
  );
}
