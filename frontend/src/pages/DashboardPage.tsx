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
import { MembershipCard } from '@/components/MembershipCard';
import { useAuth } from '@/lib/auth';
import { useMyDashboard } from '@/lib/dashboard';
import { formatDate, formatPrice, useCancelMembership } from '@/lib/memberships';
import { useMyNotifications } from '@/lib/notifications';

function membershipVariant(status: string) {
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

function checkinVariant(accepted: boolean) {
  if (accepted) return 'success' as const;
  return 'destructive' as const;
}

export function DashboardPage() {
  const { user, logout } = useAuth();
  const { data, isLoading } = useMyDashboard(Boolean(user));
  const { data: notifData } = useMyNotifications(Boolean(user));
  const cancel = useCancelMembership();
  const unread = notifData?.total ?? 0;

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Welcome back</p>
          <h1 className="text-3xl font-bold">
            {data?.user.full_name ?? user?.full_name}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link to="/notifications" aria-label="Notifications">
              Notifications
              {unread > 0 && (
                <span
                  aria-label={`${unread} unread`}
                  className="ml-2 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-xs font-semibold text-primary-foreground"
                >
                  {unread}
                </span>
              )}
            </Link>
          </Button>
          <Button variant="outline" onClick={logout}>
            Sign out
          </Button>
        </div>
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {data && (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Hero / next action */}
          <Card className="lg:col-span-3">
            <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
              <div>
                <CardTitle>
                  {data.pending_membership
                    ? 'Action needed'
                    : data.active_membership && data.expiring_today
                      ? 'Last day'
                      : data.active_membership && data.expiring_soon
                        ? 'Renewal due'
                        : data.active_membership
                          ? 'You’re all set'
                          : 'No membership'}
                </CardTitle>
                <CardDescription>
                  {data.pending_membership && (
                    <>You have an unpaid membership. Complete payment to activate.</>
                  )}
                  {!data.pending_membership &&
                    data.active_membership &&
                    data.expiring_today && <>Your plan ends today.</>}
                  {!data.pending_membership &&
                    data.active_membership &&
                    !data.expiring_today &&
                    data.expiring_soon && (
                      <>
                        Your plan ends in{' '}
                        <strong>{data.days_remaining} day(s)</strong>.
                      </>
                    )}
                  {!data.pending_membership &&
                    data.active_membership &&
                    !data.expiring_soon && (
                      <>
                        {data.days_remaining} day(s) remaining on your plan.
                      </>
                    )}
                  {!data.pending_membership && !data.active_membership && (
                    <>Pick a plan to get started.</>
                  )}
                </CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.pending_membership && (
                  <Button asChild>
                    <Link
                      to={`/checkout?membership_id=${data.pending_membership.id}`}
                    >
                      Pay now
                    </Link>
                  </Button>
                )}
                {!data.active_membership && (
                  <Button asChild>
                    <Link to="/plans">View plans</Link>
                  </Button>
                )}
                {data.active_membership && (data.expiring_soon || data.expiring_today) && (
                  <Button asChild>
                    <Link to="/plans">Renew</Link>
                  </Button>
                )}
              </div>
            </CardHeader>
          </Card>

          {/* Active membership */}
          <Card>
            <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
              <div>
                <CardTitle>Membership</CardTitle>
                <CardDescription>Active plan details.</CardDescription>
              </div>
              {data.active_membership && (
                <Badge variant={membershipVariant(data.active_membership.status)}>
                  {data.active_membership.status}
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {!data.active_membership && (
                <p className="text-sm text-muted-foreground">
                  No active membership.
                </p>
              )}
              {data.active_membership && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <p className="text-lg font-semibold">
                      {data.active_membership.plan_name || `Plan #${data.active_membership.plan_id}`}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {data.active_membership.start_date &&
                        formatDate(data.active_membership.start_date)}{' '}
                      →{' '}
                      {data.active_membership.end_date &&
                        formatDate(data.active_membership.end_date)}
                    </p>
                    <p className="text-2xl font-bold">
                      {formatPrice(
                        data.active_membership.price_cents,
                        data.active_membership.currency,
                      )}
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={cancel.isPending}
                    onClick={() => {
                      if (window.confirm('Are you sure you want to cancel your membership?')) {
                        cancel.mutate(data.active_membership.id);
                      }
                    }}
                  >
                    {cancel.isPending ? 'Cancelling…' : 'Cancel Membership'}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Check-in (QR) */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Check-in</CardTitle>
              <CardDescription>Show this QR at the front desk.</CardDescription>
            </CardHeader>
            <CardContent>
              <MembershipCard />
            </CardContent>
          </Card>

          {/* Payments */}
          <Card>
            <CardHeader>
              <CardTitle>Payments</CardTitle>
              <CardDescription>Recent activity.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Last 30 days</span>
                <span className="font-semibold">
                  {formatPrice(data.spend_30d_cents, data.currency)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">All time</span>
                <span className="font-semibold">
                  {formatPrice(data.spend_total_cents, data.currency)}
                </span>
              </div>
              <div className="space-y-2">
                {data.recent_payments.length === 0 && (
                  <p className="text-xs text-muted-foreground">
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
                        {formatDate(p.created_at)}
                      </p>
                    </div>
                    <Badge variant={paymentVariant(p.status)}>{p.status}</Badge>
                  </div>
                ))}
              </div>
              <Button asChild variant="link" size="sm" className="px-0">
                <Link to="/payments">View all payments</Link>
              </Button>
            </CardContent>
          </Card>

          {/* Check-ins */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Recent check-ins</CardTitle>
              <CardDescription>Last 5 visits.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {data.recent_checkins.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No check-ins yet — your first visit will appear here.
                </p>
              )}
              {data.recent_checkins.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between rounded border px-3 py-2 text-sm"
                >
                  <div>
                    <p className="font-medium">{formatDate(c.scanned_at)}</p>
                    {c.reason && (
                      <p className="text-xs text-muted-foreground">{c.reason}</p>
                    )}
                  </div>
                  <Badge variant={checkinVariant(c.accepted)}>
                    {c.accepted ? 'admitted' : 'denied'}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      <div className="mt-8">
        <Button asChild variant="link" className="px-0">
          <Link to="/">← Back to home</Link>
        </Button>
      </div>
    </main>
  );
}