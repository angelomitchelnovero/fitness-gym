import { Link } from 'react-router-dom';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';
import {
  formatPrice,
  useActivePlans,
  usePurchaseMembership,
} from '@/lib/memberships';
import { toApiError } from '@/lib/api';

export function PlansPage() {
  const { user } = useAuth();
  const plans = useActivePlans(Boolean(user));
  const purchase = usePurchaseMembership();

  function handleSubscribe(planId: number) {
    purchase.mutate(planId, {
      onSuccess: () => {
        window.location.href = '/dashboard';
      },
      onError: (err) => {
        window.alert(toApiError(err).message);
      },
    });
  }

  return (
    <main className="container py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Membership plans</h1>
        <p className="mt-1 text-muted-foreground">
          Choose a plan and start training today.
        </p>
      </div>

      {plans.isLoading && (
        <p className="text-sm text-muted-foreground">Loading plans…</p>
      )}
      {plans.isError && (
        <p className="text-sm text-destructive">
          {toApiError(plans.error).message}
        </p>
      )}

      {plans.data && plans.data.items.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            No plans are available right now.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {plans.data?.items.map((plan) => (
          <Card key={plan.id} className="flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{plan.name}</CardTitle>
                <Badge variant="success">Active</Badge>
              </div>
              <CardDescription>
                {plan.duration_days} days of access
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <p className="text-3xl font-bold">
                {formatPrice(plan.price_cents, plan.currency)}
              </p>
              {plan.description && (
                <p className="mt-3 text-sm text-muted-foreground">
                  {plan.description}
                </p>
              )}
            </CardContent>
            <CardFooter>
              {user ? (
                <Button
                  className="w-full"
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={purchase.isPending}
                >
                  {purchase.isPending ? 'Subscribing…' : 'Subscribe'}
                </Button>
              ) : (
                <Button asChild className="w-full">
                  <Link to="/register">Get started</Link>
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </main>
  );
}
