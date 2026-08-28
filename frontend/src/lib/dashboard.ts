import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { CustomerDashboard } from '@/types/customer-dashboard';

export function useMyDashboard(enabled = true) {
  return useQuery({
    queryKey: ['dashboard', 'me'],
    enabled,
    queryFn: async () =>
      (await api.get<CustomerDashboard>('/dashboard/me')).data,
  });
}