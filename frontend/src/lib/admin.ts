import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { DashboardSummary } from '@/types/admin';

export function useAdminDashboard(enabled = true) {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    enabled,
    queryFn: async () =>
      (await api.get<DashboardSummary>('/admin/dashboard')).data,
  });
}