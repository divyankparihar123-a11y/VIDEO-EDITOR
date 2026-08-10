export type ClipOut = {
  id: number;
  kind: "video" | "photo" | "music";
  filename: string;
  stored_path: string;
  duration_s: number | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  created_at: string;
};

export type AspectRatio = "9:16" | "16:9" | "1:1";

export type StylePreset = "cinematic" | "energetic" | "vlog" | "luxury";

export type JobCreatePayload = {
  clip_ids: number[];
  photo_ids: number[];
  music_id: number | null;
  aspect_ratio: AspectRatio;
  target_duration: number;
  style: StylePreset;
};

export type JobStatus = "queued" | "running" | "done" | "failed" | "cancelled";

export type JobOut = {
  id: number;
  status: JobStatus;
  progress_pct: number;
  current_stage: string | null;
  aspect_ratio: string;
  target_duration_s: number;
  style: string;
  output_path: string | null;
  timeline_path: string | null;
  error_message: string | null;
  warnings: string[];
  clip_ids: number[];
  photo_ids: number[];
  music_id: number | null;
  created_at: string;
  updated_at: string;
};

export type TimelineClipSegment = {
  type?: "video" | "photo";
  clip_id: number;
  source: string;
  in?: number;
  out?: number;
  duration?: number;
  kenburns_seed?: number;
};

export type TimelineMusicInfo = {
  source: string;
  tempo_bpm: number | null;
  beats: number[];
} | null;

export type TimelineColorGrade = {
  contrast: number;
  saturation: number;
  gamma: number;
  vignette: number;
} | null;

export type TimelineData = {
  target_duration: number;
  aspect_ratio: string;
  style: string;
  fps: number;
  clips: TimelineClipSegment[];
  captions?: any[];
  music?: TimelineMusicInfo;
  color_grade?: TimelineColorGrade;
  transitions?: string[];
  transition_duration?: number;
  warnings?: string[];
};

