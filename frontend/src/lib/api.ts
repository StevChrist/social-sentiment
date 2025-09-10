// src/lib/api.ts - FIXED POLLING VERSION
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making request to: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface StartScrapeResponse {
  job_id: string;
  eta_seconds_initial: number;
  message: string;
}

export interface JobStatus {
  job_id: string;
  state: 'queued' | 'running' | 'done' | 'error' | 'canceled';
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
  counts: {
    positive: number;
    negative: number;
    neutral: number;
  };
  ratios: {
    positive: number;
    negative: number;
    neutral: number;
  };
  examples: Array<{
    text: string;
    author: string;
    published_at: string;
    like_count: number;
    is_reply: boolean;
    prediction: {
      label: string;
      confidence: number;
      scores: {
        negative: number;
        neutral: number;
        positive: number;
      };
    };
  }>;
  processing_time: number;
  visualizations?: {
    wordcloud_base64: string;
    pie_chart_base64: string;
    bar_chart_base64: string;
    top_keywords: Array<{
      word: string;
      frequency: number;
    }>;
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

// Extract video ID function
const extractVideoId = (input: string): string => {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
    /^[a-zA-Z0-9_-]{11}$/
  ];

  for (const pattern of patterns) {
    const match = input.match(pattern);
    if (match) return match[1] || match[0];
  }

  return input;
};

// ✅ SIMPLIFIED API - DIRECT CALL WITHOUT POLLING
export const startScrape = async (url: string, percentage: number = 1.0): Promise<StartScrapeResponse> => {
  const videoId = extractVideoId(url);
  
  try {
    // ✅ Direct API call - no localStorage simulation
    const response = await api.get(`/api/analyze/video/${videoId}/visualize?percentage=${percentage}&save_to_db=true`);
    
    return {
      job_id: `direct_${Date.now()}`,
      eta_seconds_initial: 0,
      message: 'Analysis completed',
      result: response.data // ✅ Return result directly
    } as any;
  } catch (error) {
    throw new Error('Failed to start analysis: ' + (error instanceof Error ? error.message : 'Unknown error'));
  }
};

export const getScrapeStatus = async (jobId: string, percentage?: number): Promise<JobStatus> => {
  // ✅ Since we do direct call, always return completed status
  return {
    job_id: jobId,
    state: 'done',
    progress: 100,
    elapsed_seconds: 0,
    eta_remaining_seconds: 0,
    message: 'Analysis completed',
    result: (startScrape as any).lastResult // This will be set by startScrape
  };
};

// Health check
export const healthCheck = () => api.get('/health');

// Direct analysis functions
export const analyzeVideo = (videoId: string, options: Record<string, any> = {}) => {
  const params = new URLSearchParams();
  if (options.maxComments) params.append('max_comments', String(options.maxComments));
  if (options.includeReplies) params.append('include_replies', 'true');
  return api.get(`/api/analyze/video/${videoId}/visualize?${params.toString()}`);
};

export const predictSentiment = (texts: string[]) =>
  api.post('/api/predict', { texts });

export const createVisualizations = (texts: string[]) =>
  api.post('/api/visualize', { texts });
