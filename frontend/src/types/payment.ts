export type PaymentStatus =
  | 'pending'
  | 'succeeded'
  | 'failed'
  | 'cancelled'
  | 'refunded';

export interface Payment {
  id: number;
  user_id: number;
  membership_id: number | null;
  amount_cents: number;
  currency: string;
  provider: string;
  external_id: string | null;
  status: PaymentStatus;
  method: string | null;
  failure_reason: string | null;
  paid_at: string | null;
  created_at: string;
}

export interface PaymentListResponse {
  items: Payment[];
  total: number;
}

export interface CheckoutResponse {
  payment: Payment;
  checkout_url?: string | null;
}