"use client";

import React, { useRef, useState } from "react";
import type { ClipOut } from "@/lib/types";

interface MusicUploaderProps {
  uploading: boolean;
  music: ClipOut | null;
  onFileSelected: (file: File) => void;
  onRemove: () => void;
}

export default function MusicUploader({
  uploading,
  music,
  onFileSelected,
  onRemove,
}: MusicUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  function handleFile(file: File | undefined) {
    if (!file) return;
    onFileSelected(file);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 16 }}>🎵</span>
        Background Music
        <span className="badge badge-purple" style={{ fontSize: 11 }}>optional · beat-sync</span>
      </label>

      {music ? (
        <div className="glass-card animate-slideInLeft" style={{
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          borderRadius: 14,
          border: "1px solid hsl(271, 91%, 65%, 0.2)",
          background: "hsl(271, 91%, 65%, 0.05)"
        }}>
          {/* Waveform icon */}
          <div style={{
            width: 44, height: 44,
            background: "hsl(271, 91%, 65%, 0.15)",
            border: "1px solid hsl(271, 91%, 65%, 0.3)",
            borderRadius: 12,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, flexShrink: 0
          }}>
            🎶
          </div>

          {/* Waveform visualization */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {music.filename}
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 6 }}>
              {[3, 6, 4, 8, 5, 9, 4, 7, 3, 6, 8, 5, 4, 6, 3].map((h, i) => (
                <div key={i} style={{
                  width: 3,
                  height: h * 2,
                  background: `hsl(271, 91%, ${55 + h}%)`,
                  borderRadius: 2,
                  opacity: 0.7,
                  animation: `bounce-soft ${0.8 + i * 0.07}s ease-in-out infinite`,
                  animationDelay: `${i * 0.05}s`,
                }} />
              ))}
              {music.duration_s && (
                <span style={{ fontSize: 12, color: "var(--text-muted)", marginLeft: 8 }}>
                  {Math.floor(music.duration_s / 60)}m {Math.floor(music.duration_s % 60)}s
                </span>
              )}
            </div>
          </div>

          <button
            type="button"
            id="remove-music-btn"
            onClick={onRemove}
            aria-label="Remove music"
            style={{
              width: 30, height: 30,
              border: "none",
              background: "hsl(0,72%,51%,0.1)",
              color: "hsl(0,80%,65%)",
              borderRadius: 8,
              cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16, flexShrink: 0,
              transition: "background 0.15s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "hsl(0,72%,51%,0.2)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "hsl(0,72%,51%,0.1)")}
          >
            ×
          </button>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          style={{
            padding: "28px 24px",
            borderRadius: 14,
            border: dragActive
              ? "2px dashed var(--brand-purple)"
              : "2px dashed hsl(224, 20%, 22%)",
            background: dragActive ? "hsl(271, 91%, 65%, 0.05)" : "hsl(224, 20%, 10%)",
            cursor: uploading ? "wait" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: 16,
            transition: "all 0.2s ease",
          }}
          aria-label="Upload background music"
        >
          <div style={{
            width: 48, height: 48,
            background: "hsl(224, 20%, 15%)",
            borderRadius: 14,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, flexShrink: 0,
          }}>
            {uploading ? <span className="animate-spin-slow">⚙️</span> : "🎵"}
          </div>
          <div>
            <p style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              {uploading ? "Uploading music..." : "Add background music"}
            </p>
            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "3px 0 0" }}>
              {uploading ? "Please wait" : "MP3, WAV, AAC · AI will sync cuts to the beat"}
            </p>
          </div>
        </div>
      )}

      <input
        ref={inputRef}
        id="music-file-input"
        type="file"
        accept="audio/*"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])}
        disabled={uploading}
      />
    </div>
  );
}
