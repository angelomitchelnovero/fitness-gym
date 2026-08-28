import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toApiError } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import {
  formatDate,
  formatPrice,
  useMyMemberships,
} from '@/lib/memberships';
import { useCheckout, useVerifyPayment } from '@/lib/payments';

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

export function CheckoutPage() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const memberships = useMyMemberships(Boolean(user));
  const checkout = useCheckout();
  const verify = useVerifyPayment();

  const membershipId = Number(params.get('membership_id') ?? 0);
  const membership = useMemo(
    () => memberships.data?.items.find((m) => m.id === membershipId),
    [memberships.data, membershipId],
  );

  const [paymentId, setPaymentId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Once we have a payment, auto-verify with the mock provider.
  useEffect(() => {
    if (!paymentId) return;
    verify.mutate(
      { paymentId, forceOutcome: 'succeeded' },
      {
        onSuccess: (p) => {
          if (p.status === 'succeeded') {
            navigate('/dashboard');
          }
        },
      },
    );
    // verify object identity is unstable; only depend on the id.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paymentId, navigate]);

  const onStartCheckout = () => {
    if (!membershipId) return;
    setError(null);
    checkout.mutate(
      { membership_id: membershipId, provider: 'mock' },
      {
        onSuccess: (res) => setPaymentId(res.payment.id),
        onError: (err) => setError(toApiError(err).message),
      },
    );
  };

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Checkout</p>
          <h1 className="text-3xl font-bold">Complete payment</h1>
        </div>
        <Button asChild variant="outline">
          <Link to="/dashboard">Back to dashboard</Link>
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
            <div>
              <CardTitle>Membership</CardTitle>
              <CardDescription>Plan summary.</CardDescription>
            </div>
            {membership && (
              <Badge variant={statusVariant(membership.status)}>
                {membership.status}
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            {memberships.isLoading && (
              <p className="text-sm text-muted-foreground">Loading…</p>
            )}
            {!memberships.isLoading && !membership && (
              <p className="text-sm text-muted-foreground">
                Membership not found.
              </p>
            )}
            {membership && (
              <div className="space-y-2">
                <p className="text-lg font-semibold">
                  {membership.plan?.name ?? `Plan #${membership.plan_id}`}
                </p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(membership.start_date)} →{' '}
                  {formatDate(membership.end_date)}
                </p>
                <p className="text-2xl font-bold">
                  {formatPrice(membership.price_cents, membership.currency)}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payment</CardTitle>
            <CardDescription>
              Using the local mock provider (no real money moves).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && <p className="text-sm text-destructive">{error}</p>}
            {!paymentId && (
              <Button
                onClick={onStartCheckout}
                disabled={!membership || checkout.isPending}
              >
                {checkout.isPending ? 'Starting checkout…' : 'Pay now'}
              </Button>
            )}
            {paymentId && (
              <p className="text-sm text-muted-foreground">
                {verify.isPending
                  ? 'Verifying with provider…'
                  : verify.isSuccess
                    ? 'Payment confirmed — redirecting…'
                    : 'Awaiting verification'}
              </p>
            )}
            <Button asChild variant="ghost">
              <Link to="/dashboard">Cancel</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}