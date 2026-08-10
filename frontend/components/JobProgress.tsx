"use client";

import type { JobOut } from "@/lib/types";

interface JobProgressProps {
  job: JobOut;
}

const STAGE_EMOJIS: Record<string, string> = {
  "loading clips": "📂",
  "analyzing clip quality": "🔍",
  "transcribing captions": "📝",
  "rendering": "🎬",
  "composing transitions": "✨",
  "normalizing": "⚙️",
  "done": "✅",
  "failed": "❌",
};

function getStageEmoji(stage: string | null | undefined): string {
  if (!stage) return "⏳";
  for (const [key, emoji] of Object.entries(STAGE_EMOJIS)) {
    if (stage.toLowerCase().includes(key.toLowerCase())) return emoji;
  }
  return "⚙️";
}

function getStatusColor(status: string) {
  switch (status) {
    case "done": return "var(--brand-cyan)";
    case "failed": return "hsl(0, 80%, 65%)";
    case "cancelled": return "hsl(38, 100%, 65%)";
    case "running": return "var(--brand-purple)";
    default: return "var(--text-muted)";
  }
}

function getStatusBadgeClass(status: string) {
  switch (status) {
    case "done": return "badge badge-green";
    case "failed": return "badge badge-red";
    case "cancelled": return "badge badge-cyan";
    case "running": return "badge badge-purple";
    default: return "badge badge-cyan";
  }
}

export default function JobProgress({ job }: JobProgressProps) {
  const pct = Math.min(100, Math.max(0, job.progress_pct ?? 0));
  const isFailed = job.status === "failed";
  const isRunning = job.status === "running" || job.status === "queued";

  return (
    <div
      className="glass-card animate-fadeInUp"
      style={{ padding: 28, width: "100%", display: "flex", flexDirection: "column", gap: 20 }}
    >
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>{getStageEmoji(job.current_stage)}</span>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {isFailed ? "Job Failed" : "Rendering Reel"}
            </h2>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "2px 0 0" }}>
              {job.current_stage ?? "Queued"}
            </p>
          </div>
        </div>
        <span className={getStatusBadgeClass(job.status)}>
          {job.status.toUpperCase()}
        </span>
      </div>

      {/* Progress bar */}
      {!isFailed && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Progress</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--brand-cyan)", fontFamily: "JetBrains Mono, monospace" }}>
              {pct.toFixed(0)}%
            </span>
          </div>
          <div className="progress-track">
            <div
              className="progress-bar"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Stage timeline */}
      {!isFailed && (
        <div style={{ display: "flex", gap: 0 }}>
          {[
            { label: "Load", pct: 5 },
            { label: "Analyze", pct: 15 },
            { label: "Captions", pct: 30 },
            { label: "Render", pct: 90 },
            { label: "Done", pct: 100 },
          ].map((step, i) => {
            const done = pct >= step.pct;
            const active = !done && (i === 0 || pct >= ([5, 15, 30, 90, 100][i - 1] ?? 0));
            return (
              <div key={step.label} style={{ flex: 1, textAlign: "center" }}>
                <div style={{
                  width: 28, height: 28,
                  borderRadius: "50%",
                  background: done ? "var(--brand-cyan)" : active ? "hsl(192,100%,50%,0.2)" : "hsl(224,20%,18%)",
                  border: done ? "none" : active ? "2px solid var(--brand-cyan)" : "2px solid hsl(224,20%,25%)",
                  color: done ? "#000" : active ? "var(--brand-cyan)" : "var(--text-muted)",
                  fontSize: 12, fontWeight: 700,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  margin: "0 auto 6px",
                  transition: "all 0.4s ease",
                  boxShadow: done || active ? "0 0 12px hsl(192,100%,50%,0.3)" : "none",
                }}>
                  {done ? "✓" : i + 1}
                </div>
                <div style={{ fontSize: 10, color: done ? "var(--brand-cyan)" : "var(--text-muted)", fontWeight: done ? 600 : 400 }}>
                  {step.label}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Spinner for active */}
      {isRunning && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", background: "hsl(271,91%,65%,0.07)", border: "1px solid hsl(271,91%,65%,0.15)", borderRadius: 10 }}>
          <span className="animate-spin-slow" style={{ fontSize: 16 }}>⚙️</span>
          <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
            {job.status === "queued" ? "Job is queued — will start shortly..." : `Processing: ${job.current_stage ?? "..."}`}
          </span>
        </div>
      )}

      {/* Error */}
      {isFailed && job.error_message && (
        <div style={{
          padding: "14px 16px",
          background: "hsl(0,72%,51%,0.08)",
          border: "1px solid hsl(0,72%,51%,0.2)",
          borderRadius: 10,
        }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: "hsl(0,80%,65%)", margin: "0 0 6px" }}>
            Error Details
          </p>
          <pre style={{
            fontSize: 11,
            color: "hsl(0,50%,70%)",
            margin: 0,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            fontFamily: "JetBrains Mono, monospace",
            maxHeight: 200,
            overflowY: "auto",
          }}>
            {job.error_message}
          </pre>
        </div>
      )}

      {/* Warnings */}
      {job.warnings && job.warnings.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {job.warnings.map((w, i) => (
            <div key={i} style={{
              padding: "10px 14px",
              background: "hsl(38,100%,55%,0.08)",
              border: "1px solid hsl(38,100%,55%,0.2)",
              borderRadius: 10,
              fontSize: 13,
              color: "hsl(38,100%,70%)",
              display: "flex",
              gap: 8,
              alignItems: "flex-start",
            }}>
              <span>⚠️</span>
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
