// src/lib/api.ts
import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // default 3 menit, bisa di override per-request
  headers: { "Content-Type": "application/json" },
});

// --- Interceptors
api.interceptors.request.use(
  (config) => {
    console.log(
      `Making request to: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      console.error(
        "API Error: Request timeout – server masih memproses atau lambat"
      );
    } else {
      console.error("API Error:", error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// ===== Types =====
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
    wordcloud_base64: string;
    pie_chart_base64: string;
    bar_chart_base64: string;
    top_keywords: Array<{ word: string; frequency: number }>;
    sentiment_stats: {
      total_comments: number;
      sentiment_counts: {
        positive: number;
        negative: number;
        neutral: number;
      };
      sentiment_percentages: {
        positive: number;
        negative: number;
        neutral: number;
      };
      overall_avg_confidence: number;
    };
  };
}

// ===== Helpers =====
const extractVideoId = (input: string): string => {
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

// simpan hasil terakhir untuk getScrapeStatus
let lastResult: AnalyzeOut | undefined;

// ✅ DIRECT CALL (no polling)
export const startScrape = async (
  url: string,
  percentage: number = 1.0
): Promise<StartScrapeResponse> => {
  const videoId = extractVideoId(url);

  try {
    const response = await api.get<AnalyzeOut>(
      `/api/analyze/video/${videoId}/visualize`,
      {
        params: { percentage, save_to_db: true },
        timeout: 0, // no timeout untuk request berat
      }
    );

    lastResult = response.data;

    return {
      job_id: `direct_${Date.now()}`,
      eta_seconds_initial: 0,
      message: "Analysis completed",
      result: response.data,
    };
  } catch (error) {
    throw new Error(
      "Failed to start analysis: " +
        (error instanceof Error ? error.message : "Unknown error")
    );
  }
};

// status dummy, karena kita pakai direct call
export const getScrapeStatus = async (jobId: string): Promise<JobStatus> => {
  return {
    job_id: jobId,
    state: "done",
    progress: 100,
    elapsed_seconds: 0,
    eta_remaining_seconds: 0,
    message: "Analysis completed",
    result: lastResult,
  };
};

// Health check
export const healthCheck = () => api.get("/health");

// Direct analysis helpers
export interface AnalyzeOptions {
  maxComments?: number;
  includeReplies?: boolean;
}

export const analyzeVideo = (
  videoId: string,
  options: AnalyzeOptions = {}
) => {
  const params = new URLSearchParams();
  if (options.maxComments !== undefined)
    params.append("max_comments", String(options.maxComments));
  if (options.includeReplies) params.append("include_replies", "true");

  return api.get<AnalyzeOut>(
    `/api/analyze/video/${videoId}/visualize?${params.toString()}`
  );
};

export const predictSentiment = (texts: string[]) =>
  api.post("/api/predict", { texts });

export const createVisualizations = (texts: string[]) =>
  api.post("/api/visualize", { texts });
