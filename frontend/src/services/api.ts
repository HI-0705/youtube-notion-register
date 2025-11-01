import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// APIレスポンスの型定義
interface ApiResponse<T> {
  status: string;
  message?: string;
  data?: T;
  session_id?: string;
  error_code?: string;
}

// Collect APIの型定義
interface CollectRequest {
  url: string;
  channel_id?: string;
}

interface CollectResponseData {
  video_id: string;
  title: string;
  channel_name: string;
}

interface CollectResponse extends ApiResponse<CollectResponseData> {
  session_id: string;
}

// Analyze APIの型定義
interface AnalyzeRequest {
  session_id: string;
}

interface AnalyzeResponseData {
  summary: string;
  suggested_titles: string;
  categories: string[];
  emotions: string;
}

interface AnalyzeResponse extends ApiResponse<AnalyzeResponseData> {}

// Register APIの型定義
interface RegisterModifications {
  title: string;
  summary: string;
  categories: string[];
  emotions: string;
}

interface RegisterRequest {
  session_id: string;
  modifications: RegisterModifications;
}

interface RegisterResponseData {
  notion_url: string;
}

interface RegisterResponse extends ApiResponse<RegisterResponseData> {}

// Session APIの型定義
interface VideoMetadata {
  video_id: string;
  title: string;
  channel_name: string;
  published_at: string;
  duration: string;
  duration_seconds: number;
  view_count?: number;
  url: string;
  thumbnail_url?: string;
}

interface SessionInfo {
  session_id: string;
  timestamp: string;
  expires_at: string;
  video_data: VideoMetadata;
  transcript: string;
  transcript_language: string;
  status: "collected" | "analyzed" | "registered" | "error";
  created_by: string;
  analysis_result?: AnalyzeResponseData;
}

interface SessionResponse extends ApiResponse<SessionInfo> {}

export const api = {
  async healthCheck(): Promise<ApiResponse<null>> {
    const response = await apiClient.get<ApiResponse<null>>("/api/v1/health");
    return response.data;
  },

  async collectVideoData(request: CollectRequest): Promise<CollectResponse> {
    const response = await apiClient.post<CollectResponse>(
      "/api/v1/collect",
      request
    );
    return response.data;
  },

  async analyzeTranscript(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const response = await apiClient.post<AnalyzeResponse>(
      "/api/v1/analyze",
      request
    );
    return response.data;
  },

  async registerToNotion(request: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>(
      "/api/v1/register",
      request
    );
    return response.data;
  },

  async getSessionStatus(sessionId: string): Promise<SessionResponse> {
    const response = await apiClient.get<SessionResponse>(
      `/api/v1/session/${sessionId}`
    );
    return response.data;
  },
};
