export interface PlanBreakdownEntry {
  plan_id: number;
  plan_name: string;
  active_count: number;
}

export interface RecentPaymentEntry {
  id: number;
  user_id: number;
  membership_id: number | null;
  amount_cents: number;
  currency: string;
  status: string;
  paid_at: string | null;
  created_at: string;
}

export interface RecentMembershipEntry {
  id: number;
  user_id: number;
  plan_id: number;
  plan_name: string | null;
  status: string;
  start_date: string;
  end_date: string;
}

export interface DashboardSummary {
  active_memberships: number;
  pending_memberships: number;
  expiring_within_days: number;
  expired_last_30_days: number;
  cancelled_memberships: number;
  today_checkins_total: number;
  today_checkins_accepted: number;
  today_checkins_rejected: number;
  total_revenue_cents: number;
  currency: string;
  plan_breakdown: PlanBreakdownEntry[];
  recent_payments: RecentPaymentEntry[];
  recent_memberships: RecentMembershipEntry[];
}