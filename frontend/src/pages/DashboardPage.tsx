import { Link } from 'react-router-dom';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';
import {
  daysUntil,
  formatDate,
  formatPrice,
  useCancelMembership,
  useMyMemberships,
  useRenewMembership,
} from '@/lib/memberships';

function statusVariant(status: string) {
  switch (status) {
    case 'active':
      return 'success' as const;
    case 'pending':
      return 'warning' as const;
    case 'expired':
      return 'secondary' as const;
    case 'cancelled':
      return 'destructive' as const;
    default:
      return 'default' as const;
  }
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const memberships = useMyMemberships(Boolean(user));
  const renew = useRenewMembership();
  const cancel = useCancelMembership();

  const items = memberships.data?.items ?? [];
  const active = items.find((m) => m.status === 'active') ?? items[0];

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Welcome back</p>
          <h1 className="text-3xl font-bold">{user?.full_name}</h1>
        </div>
        <Button variant="outline" onClick={logout}>
          Sign out
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
            <div>
              <CardTitle>Membership</CardTitle>
              <CardDescription>Status and expiration.</CardDescription>
            </div>
            {active && <Badge variant={statusVariant(active.status)}>{active.status}</Badge>}
          </CardHeader>
          <CardContent>
            {memberships.isLoading && (
              <p className="text-sm text-muted-foreground">Loading…</p>
            )}
            {!memberships.isLoading && !active && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  You don't have a membership yet.
                </p>
                <Button asChild>
                  <Link to="/plans">View plans</Link>
                </Button>
              </div>
            )}
            {active && active.plan && (
              <div className="space-y-3">
                <div>
                  <p className="text-lg font-semibold">{active.plan.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Started {formatDate(active.start_date)} · ends {formatDate(active.end_date)}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {daysUntil(active.end_date) >= 0
                      ? `${daysUntil(active.end_date)} days remaining`
                      : 'Expired'}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {active.status === 'active' && (
                    <Button
                      onClick={() => renew.mutate(active.id)}
                      disabled={renew.isPending}
                    >
                      {renew.isPending ? 'Renewing…' : 'Renew'}
                    </Button>
                  )}
                  <Button asChild variant="outline">
                    <Link to="/plans">Change plan</Link>
                  </Button>
                  {(active.status === 'active' || active.status === 'pending') && (
                    <Button
                      variant="ghost"
                      onClick={() => cancel.mutate(active.id)}
                      disabled={cancel.isPending}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payments</CardTitle>
            <CardDescription>History and renewals.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Coming in Phase 4.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Check-in</CardTitle>
            <CardDescription>Show your QR at the front desk.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Coming in Phase 5.</p>
            {active && (
              <p className="mt-2 text-xs text-muted-foreground">
                Plan total: {formatPrice(active.price_cents, active.currency)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {items.length > 1 && (
        <section className="mt-8">
          <h2 className="mb-3 text-xl font-semibold">History</h2>
          <div className="space-y-2">
            {items.slice(1).map((m) => (
              <Card key={m.id}>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="text-base">
                      {m.plan?.name ?? `Plan #${m.plan_id}`}
                    </CardTitle>
                    <CardDescription>
                      {formatDate(m.start_date)} → {formatDate(m.end_date)}
                    </CardDescription>
                  </div>
                  <Badge variant={statusVariant(m.status)}>{m.status}</Badge>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>
      )}

      <div className="mt-8">
        <Button asChild variant="link" className="px-0">
          <Link to="/">← Back to home</Link>
        </Button>
      </div>
    </main>
  );
}
