"use client";

interface VideoPreviewProps {
  previewUrl: string;
  downloadUrl: string;
  posterUrl?: string;
}

export default function VideoPreview({ previewUrl, downloadUrl, posterUrl }: VideoPreviewProps) {
  return (
    <div className="animate-fadeInUp" style={{ width: "100%", display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Success banner */}
      <div style={{
        padding: "16px 20px",
        background: "hsl(142, 72%, 45%, 0.08)",
        border: "1px solid hsl(142, 72%, 45%, 0.2)",
        borderRadius: 14,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}>
        <div style={{
          width: 40, height: 40,
          background: "hsl(142, 72%, 45%, 0.15)",
          borderRadius: 12,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 22,
        }}>
          🎉
        </div>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: "hsl(142, 72%, 60%)", margin: 0 }}>
            Reel Ready!
          </h3>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: "2px 0 0" }}>
            Your highlight reel has been rendered. Preview below or download.
          </p>
        </div>
      </div>

      {/* Video Player */}
      <div className="glass-card" style={{
        overflow: "hidden",
        borderRadius: 16,
        border: "1px solid hsl(142, 72%, 45%, 0.2)",
      }}>
        <video
          id="reel-preview-player"
          src={previewUrl}
          poster={posterUrl}
          controls
          playsInline
          style={{
            width: "100%",
            display: "block",
            maxHeight: 520,
            background: "#000",
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 12 }}>
        <a
          id="download-reel-btn"
          href={downloadUrl}
          download
          className="btn-primary"
          style={{
            flex: 1,
            textDecoration: "none",
            textAlign: "center",
            padding: "14px 24px",
            borderRadius: 12,
            fontSize: 15,
          }}
        >
          <span>⬇️</span>
          Download MP4
        </a>
        <a
          id="preview-reel-btn"
          href={previewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary"
          style={{ textDecoration: "none", padding: "14px 20px", borderRadius: 12, fontSize: 14 }}
        >
          🔗 Open in new tab
        </a>
      </div>

      {/* Share tip */}
      <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", margin: 0 }}>
        💡 Tip: The downloaded file is ready to upload directly to Instagram, TikTok, or YouTube Shorts
      </p>
    </div>
  );
}
