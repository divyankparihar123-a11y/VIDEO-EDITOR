"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createJob, uploadClips, uploadMusic, uploadPhotos } from "@/lib/api";
import type { AspectRatio, ClipOut, StylePreset } from "@/lib/types";
import UploadDropzone from "@/components/UploadDropzone";
import MusicUploader from "@/components/MusicUploader";
import AspectRatioPicker from "@/components/AspectRatioPicker";
import DurationSlider from "@/components/DurationSlider";
import StylePresetPicker from "@/components/StylePresetPicker";

export default function Home() {
  const router = useRouter();

  const [clips, setClips] = useState<ClipOut[]>([]);
  const [photos, setPhotos] = useState<ClipOut[]>([]);
  const [music, setMusic] = useState<ClipOut | null>(null);

  const [uploadingClips, setUploadingClips] = useState(false);
  const [uploadingPhotos, setUploadingPhotos] = useState(false);
  const [uploadingMusic, setUploadingMusic] = useState(false);

  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const [duration, setDuration] = useState(30);
  const [style, setStyle] = useState<StylePreset>("cinematic"); // matches backend presets: cinematic|energetic|vlog|luxury

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClipFiles(files: File[]) {
    setError(null);
    setUploadingClips(true);
    try {
      const uploaded = await uploadClips(files);
      setClips((prev) => [...prev, ...uploaded]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploadingClips(false);
    }
  }

  async function handlePhotoFiles(files: File[]) {
    setError(null);
    setUploadingPhotos(true);
    try {
      const uploaded = await uploadPhotos(files);
      setPhotos((prev) => [...prev, ...uploaded]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploadingPhotos(false);
    }
  }

  async function handleMusicFile(file: File) {
    setError(null);
    setUploadingMusic(true);
    try {
      const uploaded = await uploadMusic(file);
      setMusic(uploaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploadingMusic(false);
    }
  }

  async function handleGenerate() {
    if (clips.length === 0) {
      setError("Upload at least one video clip first.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const job = await createJob({
        clip_ids: clips.map((c) => c.id),
        photo_ids: photos.map((p) => p.id),
        music_id: music?.id ?? null,
        aspect_ratio: aspectRatio,
        target_duration: duration,
        style,
      });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "40px 24px 80px", minHeight: "100vh" }}>
      {/* ── Hero ── */}
      <header className="animate-fadeInUp" style={{ marginBottom: 40 }}>
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
          <Link
            href="/jobs"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 13,
              color: "var(--text-muted)",
              textDecoration: "none",
              transition: "color 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            📋 All Reels →
          </Link>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
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
            <h1 className="gradient-text" style={{ fontSize: 32, fontWeight: 800, lineHeight: 1.15, margin: 0 }}>
              AI Auto-Reel Studio
            </h1>
          </div>
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: 15, lineHeight: 1.6, maxWidth: 520 }}>
          Drop your raw footage — AI scores quality, picks the best moments, adds captions, syncs to your music, and renders a polished highlight reel automatically.
        </p>

        {/* Feature badges */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 }}>
          {["🧠 AI quality scoring", "✂️ Smart clip selection", "📝 Auto captions", "🎵 Beat-sync", "🎨 Color grade"].map((feat, i) => (
            <span key={feat} className={`badge badge-cyan animate-fadeIn delay-${(i + 1) * 100 as 100 | 200 | 300 | 400 | 500}`} style={{ fontSize: 12, fontWeight: 500 }}>
              {feat}
            </span>
          ))}
        </div>
      </header>

      {/* ── Upload Section ── */}
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div className="animate-fadeInUp delay-100">
          <UploadDropzone
            label="Video Clips"
            accept="video/*"
            uploading={uploadingClips}
            clips={clips}
            onFilesSelected={handleClipFiles}
            onRemove={(id) => setClips((prev) => prev.filter((c) => c.id !== id))}
          />
        </div>

        <div className="animate-fadeInUp delay-200">
          <UploadDropzone
            label="Photos (optional)"
            accept="image/*"
            uploading={uploadingPhotos}
            clips={photos}
            onFilesSelected={handlePhotoFiles}
            onRemove={(id) => setPhotos((prev) => prev.filter((p) => p.id !== id))}
          />
        </div>

        <div className="animate-fadeInUp delay-300">
          <MusicUploader
            uploading={uploadingMusic}
            music={music}
            onFileSelected={handleMusicFile}
            onRemove={() => setMusic(null)}
          />
        </div>
      </div>

      {/* ── Settings ── */}
      <div className="glass-card animate-fadeInUp delay-400" style={{ marginTop: 28, padding: 28 }}>
        <h2 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 24, marginTop: 0 }}>
          Reel Settings
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          <StylePresetPicker value={style} onChange={setStyle} />
          <div style={{ height: 1, background: "var(--border-subtle)" }} />
          <AspectRatioPicker value={aspectRatio} onChange={setAspectRatio} />
          <div style={{ height: 1, background: "var(--border-subtle)" }} />
          <DurationSlider value={duration} onChange={setDuration} />
        </div>
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="animate-fadeIn" style={{
          marginTop: 20,
          padding: "14px 18px",
          background: "hsl(0,72%,51%,0.1)",
          border: "1px solid hsl(0,72%,51%,0.3)",
          borderRadius: 12,
          color: "hsl(0,80%,70%)",
          fontSize: 14,
          display: "flex",
          alignItems: "center",
          gap: 10
        }}>
          <span style={{ fontSize: 18 }}>⚠️</span>
          {error}
        </div>
      )}

      {/* ── Generate Button ── */}
      <div className="animate-fadeInUp delay-500" style={{ marginTop: 28 }}>
        <button
          id="generate-reel-btn"
          type="button"
          className="btn-primary"
          onClick={handleGenerate}
          disabled={submitting || clips.length === 0}
          style={{ width: "100%", fontSize: 16, padding: "16px 28px", borderRadius: 14 }}
        >
          {submitting ? (
            <>
              <span className="animate-spin-slow" style={{ fontSize: 18 }}>⚙️</span>
              Starting job...
            </>
          ) : (
            <>
              <span>✨</span>
              Generate Reel
              {clips.length > 0 && (
                <span style={{ marginLeft: 8, background: "hsl(0,0%,0%,0.2)", borderRadius: 99, padding: "2px 8px", fontSize: 13 }}>
                  {clips.length} clip{clips.length !== 1 ? "s" : ""}
                </span>
              )}
            </>
          )}
        </button>

        {clips.length === 0 && (
          <p style={{ textAlign: "center", fontSize: 13, color: "var(--text-muted)", marginTop: 10 }}>
            Upload at least one video clip to get started
          </p>
        )}
      </div>
    </main>
  );
}
