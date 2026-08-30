import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { Membership, MembershipListResponse, MembershipPlan, PlanListResponse } from '@/types/membership';

// ---- Plans ----

export function useActivePlans(enabled = true) {
  return useQuery({
    queryKey: ['plans', 'active'],
    enabled,
    queryFn: async () => (await api.get<PlanListResponse>('/plans')).data,
  });
}

export function useAdminPlans(enabled = true) {
  return useQuery({
    queryKey: ['plans', 'admin'],
    enabled,
    queryFn: async () => (await api.get<PlanListResponse>('/plans/admin')).data,
  });
}

interface PlanInput {
  name: string;
  description?: string | null;
  duration_days: number;
  price_cents: number;
  currency?: string;
  is_active?: boolean;
}

export function useCreatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: PlanInput) =>
      (await api.post<MembershipPlan>('/plans/admin', input)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['plans'] });
    },
  });
}

export function useUpdatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, patch }: { id: number; patch: Partial<PlanInput> }) =>
      (await api.patch<MembershipPlan>(`/plans/admin/${id}`, patch)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['plans'] });
    },
  });
}

export function useDeactivatePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) =>
      (await api.delete<MembershipPlan>(`/plans/admin/${id}`)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['plans'] });
    },
  });
}

export function useDeletePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/plans/admin/${id}/permanent`);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['plans'] });
    },
  });
}

// ---- Memberships ----

export function useMyMemberships(enabled = true) {
  return useQuery({
    queryKey: ['memberships', 'me'],
    enabled,
    queryFn: async () => (await api.get<MembershipListResponse>('/memberships/me')).data,
  });
}

export function useAdminMemberships(enabled = true) {
  return useQuery({
    queryKey: ['memberships', 'admin'],
    enabled,
    queryFn: async () =>
      (await api.get<MembershipListResponse>('/memberships/admin/list')).data,
  });
}

export function useAdminExpiring(days = 7, enabled = true) {
  return useQuery({
    queryKey: ['memberships', 'expiring', days],
    enabled,
    queryFn: async () =>
      (
        await api.get<MembershipListResponse>(`/memberships/admin/expiring?days=${days}`)
      ).data,
  });
}

export function usePurchaseMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (planId: number) =>
      (await api.post<Membership>('/memberships', { plan_id: planId })).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['memberships'] });
    },
  });
}

export function useRenewMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (membershipId: number) =>
      (await api.post<Membership>(`/memberships/${membershipId}/renew`)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['memberships'] });
    },
  });
}

export function useCancelMembership() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (membershipId: number) =>
      (await api.post<Membership>(`/memberships/${membershipId}/cancel`)).data,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['memberships'] });
    },
  });
}

// ---- Formatting helpers ----

export function formatPrice(price_cents: number, currency = 'PHP'): string {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(price_cents / 100);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function daysUntil(iso: string): number {
  const target = new Date(iso);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86_400_000);
}
