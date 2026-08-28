import { Link } from 'react-router-dom';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';
import { formatDate, formatPrice } from '@/lib/memberships';
import { useMyPayments } from '@/lib/payments';

function variantFor(status: string) {
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

export function PaymentsPage() {
  const { user } = useAuth();
  const payments = useMyPayments(Boolean(user));
  const items = payments.data?.items ?? [];

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Account</p>
          <h1 className="text-3xl font-bold">Payments</h1>
        </div>
        <Button asChild variant="outline">
          <Link to="/dashboard">Back to dashboard</Link>
        </Button>
      </div>

      {payments.isLoading && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}
      {!payments.isLoading && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No payments yet.</p>
      )}

      <div className="space-y-2">
        {items.map((p) => (
          <Card key={p.id}>
            <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
              <div>
                <CardTitle className="text-base">
                  {formatPrice(p.amount_cents, p.currency)}
                </CardTitle>
                <CardDescription>
                  {p.method ?? p.provider} · {formatDate(p.created_at)}
                </CardDescription>
              </div>
              <Badge variant={variantFor(p.status)}>{p.status}</Badge>
            </CardHeader>
            {p.failure_reason && (
              <CardContent>
                <p className="text-sm text-destructive">{p.failure_reason}</p>
              </CardContent>
            )}
          </Card>
        ))}
      </div>
    </main>
  );
}