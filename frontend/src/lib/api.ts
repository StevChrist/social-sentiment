// src/lib/api.ts — Social Sentiment API Client
import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 0, // no timeout — analysis can take a long time
  headers: { "Content-Type": "application/json" },
});

// ── Interceptors ──────────────────────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    console.log(`→ ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      console.error("API timeout");
    } else {
      console.error("API Error:", error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// ── Types ─────────────────────────────────────────────────────────────────────
export interface AnalyzeOut {
  video_id: string;
  video_title: string;
  channel_title: string;
  total_comments: number;
  actual_analyzed: number;
  percentage_analyzed: number;
  counts: { positive: number; negative: number; neutral: number };
  ratios: { positive: number; negative: number; neutral: number };
  examples: Array<{
    text: string;
    author: string;
    published_at: string;
    like_count: number;
    is_reply: boolean;
    prediction: {
      label: string;
      confidence: number;
      scores: { negative: number; neutral: number; positive: number };
    };
  }>;
  processing_time: number;
  visualizations?: {
    wordcloud_base64: string | null;
    pie_chart_base64: string | null;
    bar_chart_base64: string | null;
    top_keywords: Array<{ word: string; frequency: number }>;
  };
}

export interface StartScrapeResponse {
  job_id: string;
  eta_seconds_initial: number;
  message: string;
  result?: AnalyzeOut;
}

export interface JobStatus {
  job_id: string;
  state: "queued" | "running" | "done" | "error" | "canceled";
  progress: number;
  elapsed_seconds: number;
  eta_remaining_seconds: number;
  message: string;
  result?: AnalyzeOut;
}

export interface ProgressEvent {
  step: string;
  progress: number;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
export const extractVideoId = (input: string): string => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
    /^[a-zA-Z0-9_-]{11}$/,
  ];
  for (const pattern of patterns) {
    const match = input.match(pattern);
    if (match) return (match[1] ?? match[0]) as string;
  }
  return input;
};

// ── SSE-based streaming analysis ──────────────────────────────────────────────
/**
 * Streams analysis progress via Server-Sent Events.
 * Calls onProgress for each progress update, onResult when done.
 */
export const streamAnalysis = (
  url: string,
  percentage: number,
  onProgress: (event: ProgressEvent) => void,
  onResult: (result: AnalyzeOut) => void,
  onError: (error: string) => void
): (() => void) => {
  const videoId = extractVideoId(url);
  const streamUrl = `${API_BASE_URL}/api/analyze/video/${videoId}/stream?percentage=${percentage}`;

  const eventSource = new EventSource(streamUrl);

  eventSource.addEventListener("progress", (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as ProgressEvent;
      onProgress(data);
    } catch (_) {
      // ignore parse errors
    }
  });

  eventSource.addEventListener("result", (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as AnalyzeOut;
      onResult(data);
    } catch (_) {
      onError("Failed to parse result");
    }
    eventSource.close();
  });

  eventSource.addEventListener("error", (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onError(data.error || "Unknown error");
    } catch (_) {
      onError("Connection error");
    }
    eventSource.close();
  });

  eventSource.onerror = () => {
    onError("Connection to server lost. Make sure the backend is running.");
    eventSource.close();
  };

  // Return a cleanup function
  return () => eventSource.close();
};

// ── Direct (blocking) analysis — fallback if SSE not needed ──────────────────
let lastResult: AnalyzeOut | undefined;

export const startScrape = async (
  url: string,
  percentage: number = 1.0
): Promise<StartScrapeResponse> => {
  const videoId = extractVideoId(url);

  const response = await api.get<AnalyzeOut>(
    `/api/analyze/video/${videoId}/visualize`,
    { params: { percentage, save_to_db: true } }
  );

  lastResult = response.data;

  return {
    job_id: `direct_${Date.now()}`,
    eta_seconds_initial: 0,
    message: "Analysis completed",
    result: response.data,
  };
};

// Dummy status (direct call, no job queue)
export const getScrapeStatus = async (jobId: string): Promise<JobStatus> => ({
  job_id: jobId,
  state: "done",
  progress: 100,
  elapsed_seconds: 0,
  eta_remaining_seconds: 0,
  message: "Analysis completed",
  result: lastResult,
});

// ── Download CSV ──────────────────────────────────────────────────────────────
/**
 * Trigger a CSV download for the given video analysis.
 * Opens a download URL directly in the browser.
 */
export const downloadCSV = (videoId: string, percentage: number): void => {
  const url = `${API_BASE_URL}/api/analyze/video/${videoId}/download?percentage=${percentage}`;
  const link = document.createElement("a");
  link.href = url;
  link.download = `sentiment_${videoId}_${Math.round(percentage * 100)}pct.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// ── Health check ──────────────────────────────────────────────────────────────
export const healthCheck = () => api.get("/health");

// ── Predict (direct text prediction) ─────────────────────────────────────────
export const predictSentiment = (texts: string[]) =>
  api.post("/api/predict", { texts });
