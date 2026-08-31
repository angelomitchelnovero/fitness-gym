import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type {
  CheckoutResponse,
  Payment,
  PaymentListResponse,
} from '@/types/payment';

export function useMyPayments(enabled = true) {
  return useQuery({
    queryKey: ['payments', 'me'],
    enabled,
    queryFn: async () => (await api.get<PaymentListResponse>('/payments/me')).data,
  });
}

export function useAdminPayments(enabled = true) {
  return useQuery({
    queryKey: ['payments', 'admin'],
    enabled,
    queryFn: async () =>
      (await api.get<PaymentListResponse>('/admin/payments')).data,
  });
}

export function useCheckout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      membership_id: number;
      provider?: string;
      method?: string;
    }) =>
      (await api.post<CheckoutResponse>('/payments/checkout', input)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['payments'] });
      void qc.invalidateQueries({ queryKey: ['memberships'] });
      void qc.invalidateQueries({ queryKey: ['dashboard', 'me'] });
      void qc.invalidateQueries({ queryKey: ['admin', 'dashboard'] });
    },
  });
}

export function useVerifyPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: {
      paymentId: number;
      forceOutcome?: 'succeeded' | 'failed';
    }) => {
      const body = input.forceOutcome ? { force_outcome: input.forceOutcome } : {};
      return (
        await api.post<Payment>(`/payments/${input.paymentId}/verify`, body)
      ).data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['payments'] });
      void qc.invalidateQueries({ queryKey: ['memberships'] });
      void qc.invalidateQueries({ queryKey: ['dashboard', 'me'] });
      void qc.invalidateQueries({ queryKey: ['admin', 'dashboard'] });
    },
  });
}