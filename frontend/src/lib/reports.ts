import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type {
  ReportBucketSize,
  ReportPeriod,
  ReportsResponse,
} from '@/types/reports';

export interface ReportsQuery {
  period?: ReportPeriod;
  bucket?: ReportBucketSize;
}

export function useAdminReports({ period = 'week', bucket = 'day' }: ReportsQuery = {}) {
  return useQuery({
    queryKey: ['reports', 'admin', period, bucket],
    queryFn: async () =>
      (
        await api.get<ReportsResponse>('/admin/reports', {
          params: { period, bucket },
        })
      ).data,
  });
}
