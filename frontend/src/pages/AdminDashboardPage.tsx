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
import { useAdminDashboard } from '@/lib/admin';
import { formatDate, formatPrice } from '@/lib/memberships';

function paymentVariant(status: string) {
  switch (status) {
    case 'succeeded':
      return 'success' as const;
    case 'pending':
      return 'warning' as const;
    case 'failed':
    case 'refunded':
    case 'cancelled':
      return 'destructive' as const;
    default:
      return 'default' as const;
  }
}

function membershipVariant(status: string) {
  switch (status) {
    case 'active':
      return 'success' as const;
    case 'pending':
      return 'warning' as const;
    case 'cancelled':
      return 'destructive' as const;
    default:
      return 'secondary' as const;
  }
}

export function AdminDashboardPage() {
  const { data, isLoading } = useAdminDashboard();

  return (
    <main className="container py-12">
      <div className="mb-8">
        <p className="text-sm text-muted-foreground">Admin</p>
        <h1 className="text-3xl font-bold">Dashboard</h1>
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {data && (
        <div className="space-y-6">
          {/* KPI grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Active memberships</CardDescription>
                <CardTitle className="text-3xl">
                  {data.active_memberships}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Pending</CardDescription>
                <CardTitle className="text-3xl">
                  {data.pending_memberships}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Expiring (≤ 7 days)</CardDescription>
                <CardTitle className="text-3xl text-amber-600">
                  {data.expiring_within_days}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Expired (30 days)</CardDescription>
                <CardTitle className="text-3xl">
                  {data.expired_last_30_days}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Today's check-ins</CardDescription>
                <CardTitle className="text-3xl">
                  {data.today_checkins_total}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground">
                {data.today_checkins_accepted} admitted ·{' '}
                {data.today_checkins_rejected} rejected
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Total revenue</CardDescription>
                <CardTitle className="text-3xl">
                  {formatPrice(data.total_revenue_cents, data.currency)}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Cancelled</CardDescription>
                <CardTitle className="text-3xl">
                  {data.cancelled_memberships}
                </CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Quick actions</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Button asChild size="sm" variant="outline">
                  <Link to="/admin/plans">Plans</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to="/admin/memberships">Members</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to="/admin/payments">Payments</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to="/admin/checkins">Check-ins</Link>
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Plan breakdown + Recent activity */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Active by plan</CardTitle>
                <CardDescription>
                  Live counts grouped by membership plan.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {data.plan_breakdown.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No active memberships yet.
                  </p>
                )}
                <ul className="space-y-2">
                  {data.plan_breakdown.map((row) => (
                    <li
                      key={row.plan_id}
                      className="flex items-center justify-between rounded border px-3 py-2 text-sm"
                    >
                      <span>{row.plan_name}</span>
                      <Badge variant="secondary">{row.active_count}</Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent payments</CardTitle>
                <CardDescription>Last 5 payments.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.recent_payments.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No payments yet.
                  </p>
                )}
                {data.recent_payments.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between rounded border px-3 py-2 text-sm"
                  >
                    <div>
                      <p className="font-medium">
                        {formatPrice(p.amount_cents, p.currency)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        User #{p.user_id} · {formatDate(p.created_at)}
                      </p>
                    </div>
                    <Badge variant={paymentVariant(p.status)}>{p.status}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Recent memberships</CardTitle>
                <CardDescription>Last 5 memberships created.</CardDescription>
              </CardHeader>
              <CardContent>
                {data.recent_memberships.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No memberships yet.
                  </p>
                )}
                <ul className="space-y-2">
                  {data.recent_memberships.map((m) => (
                    <li
                      key={m.id}
                      className="flex items-center justify-between rounded border px-3 py-2 text-sm"
                    >
                      <div>
                        <p className="font-medium">
                          {m.plan_name ?? `Plan #${m.plan_id}`}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          User #{m.user_id} · {formatDate(m.start_date)} →{' '}
                          {formatDate(m.end_date)}
                        </p>
                      </div>
                      <Badge variant={membershipVariant(m.status)}>
                        {m.status}
                      </Badge>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </main>
  );
}