"use client";

import React, { useRef, useState } from "react";
import type { ClipOut } from "@/lib/types";

interface UploadDropzoneProps {
  label: string;
  accept: string;
  uploading: boolean;
  clips: ClipOut[];
  onFilesSelected: (files: File[]) => void;
  onRemove: (id: number) => void;
}

function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return "";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export default function UploadDropzone({
  label,
  accept,
  uploading,
  clips,
  onFilesSelected,
  onRemove,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const isVideo = accept.startsWith("video");
  const emoji = isVideo ? "🎥" : "🖼️";
  const hint = isVideo
    ? "MP4, MOV, AVI, MKV"
    : "JPG, PNG, WEBP";

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    onFilesSelected(Array.from(files));
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  }

  function onDragOver(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(true);
  }

  function onDragLeave() {
    setDragActive(false);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Label */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <label style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 16 }}>{emoji}</span>
          {label}
          {clips.length > 0 && (
            <span className="badge badge-cyan" style={{ fontSize: 11 }}>{clips.length}</span>
          )}
        </label>
        {clips.length > 0 && (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="btn-secondary"
            style={{ padding: "6px 14px", fontSize: 13 }}
            disabled={uploading}
          >
            + Add more
          </button>
        )}
      </div>

      {/* Drop Zone */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={`gradient-border ${dragActive ? "animate-pulse-glow" : ""}`}
        style={{
          padding: clips.length > 0 ? 0 : "36px 24px",
          borderRadius: 14,
          border: dragActive
            ? "2px dashed var(--brand-cyan)"
            : "2px dashed hsl(224, 20%, 22%)",
          background: dragActive
            ? "hsl(192, 100%, 50%, 0.05)"
            : "hsl(224, 20%, 10%)",
          cursor: uploading ? "wait" : "pointer",
          transition: "all 0.2s ease",
          display: clips.length > 0 ? "none" : "flex",
          flexDirection: "column" as const,
          alignItems: "center",
          gap: 10,
        }}
        aria-label={`Upload ${label}`}
      >
        <div style={{
          width: 52, height: 52,
          background: "hsl(224, 20%, 15%)",
          borderRadius: 14,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 24,
          transition: "transform 0.2s var(--ease-spring)",
          transform: dragActive ? "scale(1.1)" : "scale(1)",
        }}>
          {uploading ? <span className="animate-spin-slow">⚙️</span> : emoji}
        </div>
        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
            {uploading ? "Uploading..." : (dragActive ? "Drop it!" : `Drop ${label.toLowerCase()} here`)}
          </p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "4px 0 0" }}>
            {uploading ? "Please wait" : `or click to browse · ${hint}`}
          </p>
        </div>
      </div>

      {/* File Chips */}
      {clips.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {clips.map((clip) => (
            <div
              key={clip.id}
              className="glass-card animate-slideInLeft"
              style={{
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: 12,
                borderRadius: 12,
              }}
            >
              {/* Icon */}
              <div style={{
                width: 38, height: 38,
                background: "hsl(192, 100%, 50%, 0.1)",
                border: "1px solid hsl(192, 100%, 50%, 0.2)",
                borderRadius: 10,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 18, flexShrink: 0
              }}>
                {isVideo ? "🎞️" : "🖼️"}
              </div>

              {/* Info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {clip.filename}
                </p>
                <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "2px 0 0", display: "flex", gap: 8 }}>
                  {clip.duration_s != null && <span>⏱ {formatDuration(clip.duration_s)}</span>}
                  {clip.width && clip.height && <span>📐 {clip.width}×{clip.height}</span>}
                  {clip.fps && <span>🎞 {clip.fps.toFixed(0)}fps</span>}
                </p>
              </div>

              {/* Remove */}
              <button
                type="button"
                id={`remove-clip-${clip.id}`}
                onClick={(e) => { e.stopPropagation(); onRemove(clip.id); }}
                aria-label={`Remove ${clip.filename}`}
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
          ))}

          {/* Add more trigger (bottom) */}
          <div
            onClick={() => !uploading && inputRef.current?.click()}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            style={{
              padding: "12px",
              border: "2px dashed hsl(224, 20%, 22%)",
              borderRadius: 12,
              textAlign: "center",
              cursor: uploading ? "wait" : "pointer",
              color: "var(--text-muted)",
              fontSize: 13,
              transition: "all 0.2s ease",
              background: dragActive ? "hsl(192, 100%, 50%, 0.05)" : "transparent",
              borderColor: dragActive ? "var(--brand-cyan)" : undefined,
            }}
          >
            {uploading ? (
              <span className="animate-spin-slow" style={{ display: "inline-block" }}>⚙️</span>
            ) : (
              <>+ Drop more or click to add</>
            )}
          </div>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        id={`upload-input-${label.replace(/\s+/g, "-").toLowerCase()}`}
        accept={accept}
        multiple
        style={{ display: "none" }}
        onChange={(e) => handleFiles(e.target.files)}
        disabled={uploading}
      />
    </div>
  );
}
