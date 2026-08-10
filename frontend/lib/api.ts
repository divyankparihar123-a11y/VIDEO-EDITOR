import type { ClipOut, JobCreatePayload, JobOut, TimelineData } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
};

async function handleJsonResponse<T>(res: Response, action: string): Promise<T> {
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body?.detail ? ` - ${body.detail}` : "";
    } catch {
      // ignore, no JSON body
    }
    throw new Error(`${action} failed with status ${res.status}${detail}`);
  }
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  return handleJsonResponse(res, "Health check");
}

async function uploadFiles(endpoint: string, files: File[]): Promise<ClipOut[]> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const res = await fetch(`${API_BASE_URL}/api/uploads/${endpoint}`, {
    method: "POST",
    body: form,
  });
  return handleJsonResponse(res, `Upload to ${endpoint}`);
}

export function uploadClips(files: File[]): Promise<ClipOut[]> {
  return uploadFiles("clips", files);
}

export function uploadPhotos(files: File[]): Promise<ClipOut[]> {
  return uploadFiles("photos", files);
}

export async function uploadMusic(file: File): Promise<ClipOut> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/uploads/music`, {
    method: "POST",
    body: form,
  });
  return handleJsonResponse(res, "Music upload");
}

export async function createJob(payload: JobCreatePayload): Promise<JobOut> {
  const res = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJsonResponse(res, "Job creation");
}

export async function getJob(jobId: number): Promise<JobOut> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`);
  return handleJsonResponse(res, "Fetching job");
}

export async function listJobs(): Promise<JobOut[]> {
  const res = await fetch(`${API_BASE_URL}/api/jobs`);
  return handleJsonResponse(res, "Listing jobs");
}

export async function purgeJob(jobId: number): Promise<{ purged: boolean; job_id: number }> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/purge`, {
    method: "DELETE",
  });
  return handleJsonResponse(res, "Purging job");
}

export async function getJobTimeline(jobId: number): Promise<TimelineData> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/timeline`);
  return handleJsonResponse(res, "Fetching job timeline");
}

export function jobEventsUrl(jobId: number): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/events`;
}

export function jobPreviewUrl(jobId: number): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/preview`;
}

export function jobDownloadUrl(jobId: number): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/download`;
}

export function jobThumbnailUrl(jobId: number): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/thumbnail`;
}

