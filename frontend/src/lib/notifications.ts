import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type {
  Notification,
  NotificationListResponse,
  TriggerExpiryResponse,
} from '@/types/notification';

export function useMyNotifications(enabled = true) {
  return useQuery({
    queryKey: ['notifications', 'me'],
    enabled,
    queryFn: async () =>
      (await api.get<NotificationListResponse>('/notifications/me')).data,
  });
}

export function useTriggerExpiryReminders() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (days?: number) =>
      (
        await api.post<TriggerExpiryResponse>(
          `/admin/notifications/expire-soon${days ? `?days=${days}` : ''}`,
        )
      ).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function notificationVariant(
  status: Notification['status'],
): 'success' | 'warning' | 'destructive' {
  switch (status) {
    case 'sent':
      return 'success';
    case 'pending':
      return 'warning';
    case 'failed':
      return 'destructive';
  }
}

export function notificationKindLabel(kind: Notification['kind']): string {
  switch (kind) {
    case 'payment_receipt':
      return 'Payment';
    case 'membership_expiring':
      return 'Renewal';
    case 'checkin_confirmation':
      return 'Check-in';
  }
}
