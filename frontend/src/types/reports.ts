export type ReportPeriod = 'day' | 'week' | 'month';
export type ReportBucketSize = 'day' | 'week';

export interface RevenuePoint {
  period_start: string;       // ISO date — first day of the bucket
  revenue_cents: number;
  payments_count: number;
}

export interface PlanPopularity {
  plan_id: number;
  plan_name: string;
  active_members: number;
  revenue_cents: number;
}

export interface RetentionSummary {
  active: number;
  cancelled: number;
  expired: number;
  pending: number;
  total_lifetime: number;
  churn_rate: number;
}

export interface ReportsResponse {
  period: ReportPeriod;
  bucket_size: ReportBucketSize;
  currency: string;
  revenue_by_period: RevenuePoint[];
  popular_plans: PlanPopularity[];
  retention: RetentionSummary;
}
