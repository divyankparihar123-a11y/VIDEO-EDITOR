import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Auto-Reel Studio — Instant Highlight Reels",
  description: "Upload your raw footage and let AI automatically select the best moments, add captions, sync to music, and render a polished reel in minutes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#050a0f" />
      </head>
      <body style={{ background: "var(--bg-void)", color: "var(--text-primary)", minHeight: "100vh" }}>
        <div style={{ position: "relative", zIndex: 1 }}>
          {children}
        </div>
      </body>
    </html>
  );
}
