export interface DashboardUser {
  id: number;
  full_name: string;
  email: string;
}

export interface MembershipSummary {
  id: number;
  plan_id: number;
  status: string;
  start_date: string | null;
  end_date: string | null;
  price_cents: number;
  currency: string;
  activated_at: string | null;
}

export interface RecentPaymentEntry {
  id: number;
  amount_cents: number;
  currency: string;
  status: string;
  paid_at: string | null;
  created_at: string;
}

export interface RecentCheckInEntry {
  id: number;
  scanned_at: string;
  accepted: boolean;
  reason: string | null;
}

export interface CustomerDashboard {
  user: DashboardUser;
  active_membership: MembershipSummary | null;
  pending_membership: MembershipSummary | null;
  days_remaining: number | null;
  expiring_soon: boolean;
  expiring_today: boolean;
  spend_30d_cents: number;
  spend_total_cents: number;
  currency: string;
  recent_payments: RecentPaymentEntry[];
  recent_checkins: RecentCheckInEntry[];
}