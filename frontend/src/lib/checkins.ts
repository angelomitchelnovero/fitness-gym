import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type {
  CardResponse,
  CheckInListResponse,
  ScanOutcome,
} from '@/types/checkin';

export function useMyCard(enabled = true) {
  return useQuery({
    queryKey: ['checkin', 'card'],
    enabled,
    queryFn: async () => (await api.get<CardResponse>('/checkin/card')).data,
    refetchInterval: 240_000, // refresh near the 5-minute expiry
    retry: false,
  });
}

export function useMyCheckins(enabled = true) {
  return useQuery({
    queryKey: ['checkin', 'me'],
    enabled,
    queryFn: async () =>
      (await api.get<CheckInListResponse>('/checkin/me')).data,
  });
}

export function useAdminCheckins(dateIso?: string, enabled = true) {
  const query = dateIso ? `?on_date=${encodeURIComponent(dateIso)}` : '';
  return useQuery({
    queryKey: ['checkin', 'admin', dateIso ?? 'today'],
    enabled,
    queryFn: async () =>
      (await api.get<CheckInListResponse>(`/admin/checkins${query}`)).data,
  });
}

export function useScan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: { token: string; source?: 'qr' | 'manual' }) =>
      (await api.post<ScanOutcome>('/checkin/scan', {
        token: input.token,
        source: input.source ?? 'qr',
      })).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['checkin'] });
    },
  });
}