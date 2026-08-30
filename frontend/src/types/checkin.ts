export interface CardResponse {
  token: string;
  membership_id: number;
  user_id: number;
  plan_name: string;
  issued_at: string;
  expires_at: string;
}

export interface CheckIn {
  id: number;
  user_id: number;
  membership_id: number | null;
  scanned_at: string;
  source: 'qr' | 'manual';
  accepted: boolean;
  reason: string | null;
}

export interface CheckInListResponse {
  items: CheckIn[];
  total: number;
}

export interface ScanOutcome {
  accepted: boolean;
  reason: string | null;
  user_id: number | null;
  membership_id: number | null;
  scanned_at: string;
  check_in_id: number;
}