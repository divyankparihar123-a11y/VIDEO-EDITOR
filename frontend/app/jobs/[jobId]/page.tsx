"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getJob, jobDownloadUrl, jobEventsUrl, jobPreviewUrl, jobThumbnailUrl, API_BASE_URL } from "@/lib/api";
import type { JobOut } from "@/lib/types";
import JobProgress from "@/components/JobProgress";
import VideoPreview from "@/components/VideoPreview";
import TimelineInspector from "@/components/TimelineInspector";

const TERMINAL = new Set(["done", "failed", "cancelled"]);


export default function JobPage({ params }: { params: { jobId: string } }) {
  const { jobId } = params;
  const jobIdNum = Number(jobId);

  const [job, setJob] = useState<JobOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    let es: EventSource | null = null;
    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | undefined;

    // --- SSE path ---
    if (typeof EventSource !== "undefined") {
      es = new EventSource(jobEventsUrl(jobIdNum));

      es.addEventListener("job_update", (e: MessageEvent) => {
        if (cancelled) return;
        try {
          const latest: JobOut = JSON.parse(e.data);
          setJob(latest);
          if (TERMINAL.has(latest.status)) {
            es?.close();
          }
        } catch {
          // ignore malformed frames
        }
      });

      es.addEventListener("error", () => {
        // SSE connection dropped — fall back to a one-shot fetch so the user
        // isn't left staring at a stale state.
        es?.close();
        if (!cancelled) {
          getJob(jobIdNum).then(setJob).catch(() => {});
        }
      });

      return () => {
        cancelled = true;
        es?.close();
      };
    }

    // --- Polling fallback (browsers without EventSource, e.g. very old Safari) ---
    async function poll() {
      try {
        const latest = await getJob(jobIdNum);
        if (cancelled) return;
        setJob(latest);
        if (!TERMINAL.has(latest.status)) {
          pollTimer = setTimeout(poll, 1500);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    }
    poll();
    return () => {
      cancelled = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [jobIdNum]);

  async function handleCancel() {
    setCancelling(true);
    try {
      await fetch(`${API_BASE_URL}/api/jobs/${jobIdNum}`, { method: "DELETE" });
      // The SSE stream will pick up the cancelled status automatically.
    } catch {
      // best effort
    } finally {
      setCancelling(false);
    }
  }

  const isActive = job && !TERMINAL.has(job.status);

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "40px 24px 80px", minHeight: "100vh" }}>
      {/* Header */}
      <header className="animate-fadeInUp" style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <Link
            href="/"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              fontSize: 14,
              color: "var(--text-muted)",
              textDecoration: "none",
              transition: "color 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            ← New reel
          </Link>
          <Link
            href="/jobs"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 14,
              color: "var(--text-muted)",
              textDecoration: "none",
              transition: "color 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            All reels →
          </Link>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 44, height: 44,
            background: "linear-gradient(135deg, var(--brand-cyan), var(--brand-purple))",
            borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, boxShadow: "0 4px 20px hsl(192,100%,50%,0.35)",
            flexShrink: 0
          }}>
            🎬
          </div>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0 }}>
              <span className="gradient-text">Reel Job</span>
              <span style={{ color: "var(--text-muted)", fontWeight: 400, marginLeft: 10, fontSize: 20 }}>
                #{jobId}
              </span>
            </h1>
            {job && (
              <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "4px 0 0" }}>
                {job.style} · {job.aspect_ratio} · {job.target_duration_s}s target
              </p>
            )}
          </div>
        </div>
      </header>

      {/* Error connecting */}
      {error && (
        <div className="animate-fadeIn" style={{
          padding: "14px 18px",
          background: "hsl(0,72%,51%,0.1)",
          border: "1px solid hsl(0,72%,51%,0.3)",
          borderRadius: 12,
          color: "hsl(0,80%,70%)",
          fontSize: 14,
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 20,
        }}>
          <span>⚠️</span>
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {!job && !error && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[80, 120, 60].map((h, i) => (
            <div key={i} className="shimmer" style={{
              height: h, borderRadius: 14,
              opacity: 0.4,
            }} />
          ))}
        </div>
      )}

      {/* Progress / Result */}
      {job && job.status !== "done" && <JobProgress job={job} />}
      {job && job.status === "done" && (
        <>
          <VideoPreview
            previewUrl={jobPreviewUrl(jobIdNum)}
            downloadUrl={jobDownloadUrl(jobIdNum)}
            posterUrl={jobThumbnailUrl(jobIdNum)}
          />
          <TimelineInspector jobId={jobIdNum} />
        </>
      )}

      {/* Cancel button */}
      {isActive && (
        <div className="animate-fadeIn" style={{ marginTop: 20, textAlign: "center" }}>
          <button
            id="cancel-job-btn"
            type="button"
            className="btn-secondary"
            onClick={handleCancel}
            disabled={cancelling}
            style={{ fontSize: 13, padding: "8px 20px", opacity: cancelling ? 0.6 : 1 }}
          >
            {cancelling ? "Cancelling…" : "✕ Cancel job"}
          </button>
        </div>
      )}
    </main>
  );
}
