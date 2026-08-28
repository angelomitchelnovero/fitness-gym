export type MembershipStatus = 'pending' | 'active' | 'expired' | 'cancelled';

export interface MembershipPlan {
  id: number;
  name: string;
  description: string | null;
  duration_days: number;
  price_cents: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Membership {
  id: number;
  user_id: number;
  plan_id: number;
  start_date: string;
  end_date: string;
  status: MembershipStatus;
  price_cents: number;
  currency: string;
  activated_at: string | null;
  created_at: string;
  plan?: MembershipPlan;
}

export interface MembershipListResponse {
  items: Membership[];
  total: number;
}

export interface PlanListResponse {
  items: MembershipPlan[];
  total: number;
}
