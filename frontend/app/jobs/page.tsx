"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { jobThumbnailUrl, listJobs, purgeJob } from "@/lib/api";
import type { JobOut } from "@/lib/types";

const TERMINAL = new Set(["done", "failed", "cancelled"]);

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    done: "badge badge-green",
    failed: "badge badge-red",
    cancelled: "badge badge-cyan",
    running: "badge badge-purple",
    queued: "badge badge-cyan",
  };
  return (
    <span className={map[status] ?? "badge badge-cyan"} style={{ fontSize: 11 }}>
      {status.toUpperCase()}
    </span>
  );
}

function JobRow({ job, onPurge }: { job: JobOut; onPurge: (id: number) => void }) {
  const pct = Math.min(100, Math.max(0, job.progress_pct ?? 0));
  const isActive = !TERMINAL.has(job.status);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDeleting(true);
    try {
      await purgeJob(job.id);
      onPurge(job.id);
    } catch (err) {
      alert(`Could not delete job: ${err instanceof Error ? err.message : String(err)}`);
      setDeleting(false);
      setConfirmDelete(false);
    }
  }

  return (
    <Link
      href={`/jobs/${job.id}`}
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <div
        className="glass-card"
        style={{
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
          cursor: "pointer",
          transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "0 8px 40px hsl(192,100%,50%,0.12)";
          (e.currentTarget as HTMLDivElement).style.borderColor = "hsl(192,100%,50%,0.3)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = "";
          (e.currentTarget as HTMLDivElement).style.boxShadow = "";
          (e.currentTarget as HTMLDivElement).style.borderColor = "";
        }}
      >
        {/* Top row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
            {/* Thumbnail Poster / Icon */}
            {job.status === "done" ? (
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: 10,
                  overflow: "hidden",
                  background: "#000",
                  flexShrink: 0,
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <img
                  src={jobThumbnailUrl(job.id)}
                  alt={`Reel #${job.id} thumbnail`}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  onError={(e) => {
                    // fallback if thumbnail image fails
                    (e.currentTarget as HTMLElement).style.display = "none";
                  }}
                />
              </div>
            ) : (
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 10,
                  background: "hsl(224, 20%, 16%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 20,
                  flexShrink: 0,
                }}
              >
                {job.status === "failed" ? "❌" : job.status === "cancelled" ? "⛔" : "⚙️"}
              </div>
            )}

            <div style={{ minWidth: 0 }}>
              <p style={{ fontSize: 15, fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                Reel #{job.id}
              </p>
              <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "2px 0 0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {job.style} · {job.aspect_ratio} · {job.target_duration_s}s · {fmtDate(job.created_at)}
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
            <StatusBadge status={job.status} />

            {/* Purge Delete Button */}
            {!confirmDelete ? (
              <button
                type="button"
                title="Delete reel and remove files"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setConfirmDelete(true);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: 14,
                  cursor: "pointer",
                  padding: "4px 6px",
                  borderRadius: 6,
                  transition: "color 0.2s ease, background 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.color = "hsl(0, 80%, 65%)";
                  (e.currentTarget as HTMLButtonElement).style.background = "hsl(0, 72%, 51%, 0.1)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
                  (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                }}
              >
                🗑️
              </button>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: 6 }} onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  disabled={deleting}
                  onClick={handleDelete}
                  style={{
                    background: "hsl(0, 72%, 51%, 0.2)",
                    border: "1px solid hsl(0, 72%, 51%, 0.4)",
                    color: "hsl(0, 80%, 70%)",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 8px",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  {deleting ? "Purging…" : "Delete"}
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setConfirmDelete(false);
                  }}
                  style={{
                    background: "hsl(224, 20%, 20%)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-muted)",
                    fontSize: 11,
                    padding: "3px 8px",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Progress bar — only for active jobs */}
        {isActive && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                {job.current_stage ?? "Queued"}
              </span>
              <span style={{ fontSize: 11, color: "var(--brand-cyan)", fontFamily: "JetBrains Mono, monospace" }}>
                {pct.toFixed(0)}%
              </span>
            </div>
            <div className="progress-track">
              <div className="progress-bar" style={{ width: `${pct}%` }} />
            </div>
          </div>
        )}

        {/* Warnings count */}
        {job.warnings && job.warnings.length > 0 && (
          <p style={{ fontSize: 11, color: "hsl(38,100%,65%)", margin: 0 }}>
            ⚠️ {job.warnings.length} warning{job.warnings.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>
    </Link>
  );
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);


  useEffect(() => {
    let unmounted = false;

    async function fetchJobs(isInitial = false) {
      if (isInitial) setLoading(true);
      try {
        const data = await listJobs();
        if (!unmounted) {
          setJobs(data);
          setError(null);
        }
      } catch (err) {
        if (!unmounted) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (isInitial && !unmounted) setLoading(false);
      }
    }

    async function tick() {
      await fetchJobs(false);
      if (!unmounted) timerRef.current = setTimeout(tick, 3000);
    }

    fetchJobs(true).then(() => {
      if (!unmounted) timerRef.current = setTimeout(tick, 3000);
    });

    return () => {
      unmounted = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const activeCount = jobs.filter((j) => !TERMINAL.has(j.status)).length;

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "40px 24px 80px", minHeight: "100vh" }}>
      {/* Header */}
      <header className="animate-fadeInUp" style={{ marginBottom: 36 }}>
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

          <Link href="/" className="btn-primary" style={{ fontSize: 13, padding: "9px 18px", borderRadius: 10, textDecoration: "none" }}>
            ✨ New Reel
          </Link>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 44, height: 44,
            background: "linear-gradient(135deg, var(--brand-cyan), var(--brand-purple))",
            borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, boxShadow: "0 4px 20px hsl(192,100%,50%,0.35)",
            flexShrink: 0,
          }}>
            📋
          </div>
          <div>
            <h1 className="gradient-text" style={{ fontSize: 28, fontWeight: 800, lineHeight: 1.15, margin: 0 }}>
              All Reels
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: 13, margin: "4px 0 0" }}>
              {jobs.length} job{jobs.length !== 1 ? "s" : ""}
              {activeCount > 0 && (
                <span style={{ marginLeft: 10, color: "var(--brand-purple)" }}>
                  · {activeCount} in progress
                </span>
              )}
            </p>
          </div>
        </div>
      </header>

      {/* Error */}
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
          Could not load jobs: {error}
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[90, 90, 90].map((h, i) => (
            <div key={i} className="shimmer" style={{ height: h, borderRadius: 14, opacity: 0.4 }} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && jobs.length === 0 && (
        <div className="glass-card animate-fadeIn" style={{
          padding: "56px 32px",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 16,
        }}>
          <div style={{ fontSize: 48 }}>🎬</div>
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>No reels yet</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: 14, margin: 0, maxWidth: 340 }}>
            Drop your footage on the home page and click Generate Reel to create your first AI-edited highlight.
          </p>
          <Link href="/" className="btn-primary" style={{ marginTop: 8, textDecoration: "none", borderRadius: 12 }}>
            ✨ Create First Reel
          </Link>
        </div>
      )}

      {/* Job list */}
      {!loading && jobs.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {jobs.map((job, i) => (
            <div
              key={job.id}
              className={`animate-fadeInUp delay-${(Math.min(i, 4) + 1) * 100 as 100 | 200 | 300 | 400 | 500}`}
            >
              <JobRow job={job} onPurge={(id) => setJobs((prev) => prev.filter((j) => j.id !== id))} />
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
