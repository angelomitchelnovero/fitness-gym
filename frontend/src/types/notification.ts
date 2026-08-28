export type NotificationStatus = 'pending' | 'sent' | 'failed';

export type NotificationKind =
  | 'payment_receipt'
  | 'membership_expiring'
  | 'checkin_confirmation';

export interface Notification {
  id: number;
  user_id: number;
  channel: string;
  kind: NotificationKind;
  subject: string;
  body: string;
  recipient: string;
  status: NotificationStatus;
  sent_at: string | null;
  error: string | null;
  related_payment_id: number | null;
  related_membership_id: number | null;
  related_check_in_id: number | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
}

export interface TriggerExpiryResponse {
  sent: number;
}
