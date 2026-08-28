import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { formatPrice } from '@/lib/memberships';
import {
  type ReportsQuery,
  useAdminReports,
} from '@/lib/reports';
import type {
  ReportBucketSize,
  ReportPeriod,
  RevenuePoint,
} from '@/types/reports';

const PERIODS: ReportPeriod[] = ['day', 'week', 'month'];

function SparkBars({
  points,
  currency,
}: {
  points: RevenuePoint[];
  currency: string;
}) {
  const max = points.reduce((m, p) => Math.max(m, p.revenue_cents), 0);
  const items = points;

  if (max === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No revenue in this window.
      </p>
    );
  }

  return (
    <div className="flex h-40 items-end gap-2">
      {items.map((p) => {
        const h = Math.max(2, Math.round((p.revenue_cents / max) * 100));
        return (
          <div
            key={p.period_start}
            className="flex flex-1 flex-col items-center gap-1"
            aria-label={`${p.period_start}: ${formatPrice(p.revenue_cents, currency)} (${p.payments_count} payments)`}
          >
            <div
              className="w-full rounded-t bg-primary/70 hover:bg-primary"
              style={{ height: `${h}%` }}
            />
            <span className="text-[10px] text-muted-foreground">
              {p.period_start.slice(5)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function PercentBar({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span>{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2 w-full rounded bg-muted">
        <div
          className="h-2 rounded bg-primary"
          style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }}
        />
      </div>
    </div>
  );
}

export function ReportsPage() {
  const [{ period, bucket }, setQuery] = useState<Required<ReportsQuery>>({
    period: 'week',
    bucket: 'day',
  });
  const { data, isLoading } = useAdminReports({ period, bucket });

  const revenueTotal = useMemo(
    () =>
      data?.revenue_by_period.reduce(
        (sum, p) => sum + p.revenue_cents,
        0,
      ) ?? 0,
    [data],
  );
  const paymentsTotal = useMemo(
    () =>
      data?.revenue_by_period.reduce(
        (sum, p) => sum + p.payments_count,
        0,
      ) ?? 0,
    [data],
  );

  const setPeriod = (p: ReportPeriod) =>
    setQuery((prev) => ({ ...prev, period: p }));
  const setBucket = (b: ReportBucketSize) =>
    setQuery((prev) => ({ ...prev, bucket: b }));

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Admin</p>
          <h1 className="text-3xl font-bold">Reports</h1>
        </div>
      </div>

      {/* Period toggle */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-widest text-muted-foreground">
          Range
        </span>
        {PERIODS.map((p) => (
          <Button
            key={p}
            size="sm"
            variant={period === p ? 'default' : 'outline'}
            onClick={() => setPeriod(p)}
          >
            {p}
          </Button>
        ))}
        {period !== 'day' && (
          <>
            <span className="ml-4 text-xs uppercase tracking-widest text-muted-foreground">
              Granularity
            </span>
            <Button
              size="sm"
              variant={bucket === 'day' ? 'default' : 'outline'}
              onClick={() => setBucket('day')}
            >
              day
            </Button>
            <Button
              size="sm"
              variant={bucket === 'week' ? 'default' : 'outline'}
              onClick={() => setBucket('week')}
            >
              week
            </Button>
          </>
        )}
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {data && (
        <div className="space-y-6">
          {/* Top KPI strip */}
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Revenue</CardDescription>
                <CardTitle className="text-3xl">
                  {formatPrice(revenueTotal, data.currency)}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground">
                {data.period} window
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Payments</CardDescription>
                <CardTitle className="text-3xl">{paymentsTotal}</CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground">
                succeeded payments in window
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Churn</CardDescription>
                <CardTitle className="text-3xl">
                  {(data.retention.churn_rate * 100).toFixed(1)}%
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground">
                cancelled ÷ lifetime members
              </CardContent>
            </Card>
          </div>

          {/* Revenue chart */}
          <Card>
            <CardHeader>
              <CardTitle>Revenue by period</CardTitle>
              <CardDescription>
                Bucketed at {data.bucket_size}. Empty days show as 0.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SparkBars
                points={data.revenue_by_period}
                currency={data.currency}
              />
            </CardContent>
          </Card>

          {/* Retention */}
          <Card>
            <CardHeader>
              <CardTitle>Retention</CardTitle>
              <CardDescription>
                All-time membership counts and churn.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Active</span>
                  <span className="font-semibold">
                    {data.retention.active}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Cancelled</span>
                  <span className="font-semibold">
                    {data.retention.cancelled}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Expired</span>
                  <span className="font-semibold">
                    {data.retention.expired}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Pending</span>
                  <span className="font-semibold">
                    {data.retention.pending}
                  </span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span>Lifetime total</span>
                  <span className="font-semibold">
                    {data.retention.total_lifetime}
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <PercentBar
                  value={data.retention.churn_rate}
                  label="Churn rate"
                />
                <p className="text-xs text-muted-foreground">
                  Churn = cancelled ÷ lifetime members.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Popular plans */}
          <Card>
            <CardHeader>
              <CardTitle>Popular plans</CardTitle>
              <CardDescription>
                Top 10 by active members, with period revenue.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data.popular_plans.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No active memberships yet.
                </p>
              )}
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2">Plan</th>
                    <th className="py-2 text-right">Active</th>
                    <th className="py-2 text-right">Revenue ({data.period})</th>
                  </tr>
                </thead>
                <tbody>
                  {data.popular_plans.map((p) => (
                    <tr key={p.plan_id} className="border-b last:border-0">
                      <td className="py-2">
                        <span className="font-medium">{p.plan_name}</span>
                      </td>
                      <td className="py-2 text-right">
                        <Badge variant="secondary">{p.active_members}</Badge>
                      </td>
                      <td className="py-2 text-right font-semibold">
                        {formatPrice(p.revenue_cents, data.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="mt-8">
        <Button asChild variant="link" className="px-0">
          <Link to="/admin">← Back to admin</Link>
        </Button>
      </div>
    </main>
  );
}
