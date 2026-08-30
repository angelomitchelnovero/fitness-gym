import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { UserListResponse, UserSummary, UserUpdate } from '@/types/admin';

export function useAdminUsers(role?: string, limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['admin', 'users', { role, limit, offset }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (role) params.append('role', role);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());
      const res = await api.get<UserListResponse>(`/users?${params.toString()}`);
      return res.data;
    },
  });
}

export function useCreateUser() {
  return useMutation({
    mutationFn: async (payload: { email: string; full_name: string; phone?: string; password?: string }) => {
      const res = await api.post<UserSummary>('/users', payload);
      return res.data;
    },
  });
}

export function useUpdateUser() {
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UserUpdate }) => {
      const res = await api.patch<UserSummary>(`/users/${id}`, payload);
      return res.data;
    },
  });
}

export function useDeleteUser() {
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/users/${id}`);
    },
  });
}
