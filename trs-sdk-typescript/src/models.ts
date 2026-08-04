export interface HealthStatus {
  status: string;
  runtime: string;
  node: string;
}

export interface SubmitResult {
  accepted: boolean;
  record_id: string;
  errors: string[];
}

export interface SyncResult {
  accepted_count: number;
  rejected_count: number;
  appended_ids: string[];
  rejected_errors: string[][];
}

