export interface Video {
  id: string;
  filename: string;
  title: string | null;
  description: string | null;
  category: string;
  is_shared: boolean;
  status: "pending" | "processing" | "completed" | "failed";
  s3_key: string | null;
  created_at: string;
  owner_id: number;
  file_size: number;
  is_deleted: boolean;
  owner_email?: string;
  summary?: string | null;
}

export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  created_at: string;
  storage_limit: number;
}

export interface SummaryResult {
  summary: string | null;
  status: "ready" | "generating";
}
