"use client";

import { useEffect, useState } from "react";
import { getJobTimeline } from "@/lib/api";
import type { TimelineClipSegment, TimelineData } from "@/lib/types";

interface TimelineInspectorProps {
  jobId: number;
}

export default function TimelineInspector({ jobId }: TimelineInspectorProps) {
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<boolean>(false);

  useEffect(() => {
    let unmounted = false;
    getJobTimeline(jobId)
      .then((data) => {
        if (!unmounted) {
          setTimeline(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!unmounted) {
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!unmounted) setLoading(false);
      });

    return () => {
      unmounted = true;
    };
  }, [jobId]);

  if (loading) {
    return (
      <div className="glass-card animate-fadeIn" style={{ padding: 18, borderRadius: 14 }}>
        <div className="shimmer" style={{ height: 24, borderRadius: 8, opacity: 0.4 }} />
      </div>
    );
  }

  if (error || !timeline) {
    return null; // hide if timeline isn't available
  }

  const clips = timeline.clips || [];
  const totalDuration = timeline.target_duration || 1;
  const music = timeline.music;
  const beats = music?.beats || [];
  const colorGrade = timeline.color_grade;

  // Calculate duration of each clip segment
  const getSegDuration = (seg: TimelineClipSegment) => {
    if (seg.type === "photo") return seg.duration || 3;
    if (seg.in !== undefined && seg.out !== undefined) return Math.max(0.1, seg.out - seg.in);
    return 1;
  };

  const totalSegmentsDuration = clips.reduce((acc, seg) => acc + getSegDuration(seg), 0);
  const scaleDuration = Math.max(totalDuration, totalSegmentsDuration);

  return (
    <div className="glass-card animate-fadeInUp" style={{ borderRadius: 16, overflow: "hidden", marginTop: 20 }}>
      {/* Header / Toggle */}
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        style={{
          width: "100%",
          padding: "16px 20px",
          background: "transparent",
          border: "none",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          color: "var(--text-primary)",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 18 }}>📊</span>
          <div>
            <h4 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Timeline Inspector</h4>
            <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "2px 0 0" }}>
              {clips.length} segment{clips.length !== 1 ? "s" : ""} · {timeline.style} style · {scaleDuration.toFixed(1)}s timeline
            </p>
          </div>
        </div>
        <span style={{ fontSize: 14, color: "var(--text-muted)", transition: "transform 0.2s ease", transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}>
          ▼
        </span>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div style={{ padding: "0 20px 20px 20px", display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ height: 1, background: "var(--border-subtle)" }} />

          {/* Timeline Visual Track */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, alignItems: "center" }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                Edit Sequence (Cut Points)
              </span>
              <div style={{ display: "flex", gap: 12, fontSize: 11, color: "var(--text-muted)" }}>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: "var(--brand-cyan)" }} />
                  Video
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: "var(--brand-purple)" }} />
                  Photo (Ken Burns)
                </span>
              </div>
            </div>

            {/* Track container */}
            <div
              style={{
                width: "100%",
                background: "hsl(224,22%,10%)",
                borderRadius: 10,
                padding: 6,
                border: "1px solid var(--border-subtle)",
                display: "flex",
                gap: 4,
                overflowX: "auto",
              }}
            >
              {clips.map((seg, idx) => {
                const segDur = getSegDuration(seg);
                const pct = (segDur / scaleDuration) * 100;
                const isPhoto = seg.type === "photo";

                return (
                  <div
                    key={idx}
                    title={`Segment ${idx + 1}: ${isPhoto ? "Photo" : "Video Clip #" + seg.clip_id} (${segDur.toFixed(1)}s)`}
                    style={{
                      flex: `0 0 ${Math.max(pct, 5)}%`,
                      minWidth: 44,
                      background: isPhoto ? "hsl(271,91%,65%,0.18)" : "hsl(192,100%,50%,0.18)",
                      border: `1px solid ${isPhoto ? "hsl(271,91%,65%,0.4)" : "hsl(192,100%,50%,0.4)"}`,
                      borderRadius: 8,
                      padding: "8px 6px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      alignItems: "center",
                      fontSize: 10,
                      fontWeight: 600,
                      color: isPhoto ? "var(--brand-purple)" : "var(--brand-cyan)",
                      textAlign: "center",
                      transition: "transform 0.15s ease",
                    }}
                  >
                    <span>{isPhoto ? "🖼️ Photo" : `📹 #${seg.clip_id}`}</span>
                    <span style={{ fontSize: 9, color: "var(--text-muted)", marginTop: 2, fontFamily: "JetBrains Mono, monospace" }}>
                      {segDur.toFixed(1)}s
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Beat Markers Track (if present) */}
          {beats.length > 0 && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                  🎵 Audio Beat Sync ({music?.tempo_bpm ? `${Math.round(music.tempo_bpm)} BPM` : "Detected Beats"})
                </span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {beats.length} beat marks
                </span>
              </div>
              <div
                style={{
                  height: 24,
                  width: "100%",
                  background: "hsl(224,22%,10%)",
                  borderRadius: 8,
                  border: "1px solid var(--border-subtle)",
                  position: "relative",
                  overflow: "hidden",
                }}
              >
                {beats.map((t, idx) => {
                  const pct = (t / scaleDuration) * 100;
                  if (pct > 100) return null;
                  return (
                    <div
                      key={idx}
                      title={`Beat at ${t.toFixed(2)}s`}
                      style={{
                        position: "absolute",
                        left: `${pct}%`,
                        top: 0,
                        bottom: 0,
                        width: 2,
                        background: "hsl(316, 83%, 64%)",
                        boxShadow: "0 0 4px hsl(316, 83%, 64%)",
                      }}
                    />
                  );
                })}
              </div>
            </div>
          )}

          {/* Metadata Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
            <div style={{ background: "hsl(224,20%,14%)", padding: "10px 14px", borderRadius: 10, border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>Color Grade</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                {colorGrade
                  ? `C:${colorGrade.contrast} S:${colorGrade.saturation} G:${colorGrade.gamma}`
                  : "Standard"}
              </span>
            </div>

            <div style={{ background: "hsl(224,20%,14%)", padding: "10px 14px", borderRadius: 10, border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>Transitions</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                {timeline.transitions ? `${timeline.transitions.join(", ")} (${timeline.transition_duration || 0.4}s)` : "Cut"}
              </span>
            </div>

            <div style={{ background: "hsl(224,20%,14%)", padding: "10px 14px", borderRadius: 10, border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", display: "block" }}>Captions</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                {timeline.captions && timeline.captions.length > 0
                  ? `${timeline.captions.length} cards`
                  : "None / Not burned"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
