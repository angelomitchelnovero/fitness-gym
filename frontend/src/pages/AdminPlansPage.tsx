import { useState, type FormEvent } from 'react';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toApiError } from '@/lib/api';
import {
  formatPrice,
  useAdminPlans,
  useCreatePlan,
  useDeactivatePlan,
} from '@/lib/memberships';

export function AdminPlansPage() {
  const plans = useAdminPlans(true);
  const create = useCreatePlan();
  const deactivate = useDeactivatePlan();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState('30');
  const [price, setPrice] = useState('1500');

  function handleCreate(e: FormEvent) {
    e.preventDefault();
    create.mutate(
      {
        name: name.trim(),
        description: description.trim() || null,
        duration_days: Number(duration),
        price_cents: Math.round(Number(price) * 100),
      },
      {
        onSuccess: () => {
          setName('');
          setDescription('');
          setDuration('30');
          setPrice('1500');
        },
        onError: (err) => window.alert(toApiError(err).message),
      },
    );
  }

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold">Membership plans</h1>
          <p className="mt-1 text-muted-foreground">Manage plans customers can buy.</p>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        <section>
          <h2 className="mb-4 text-xl font-semibold">Existing plans</h2>
          {plans.isLoading && (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
          {plans.data && plans.data.items.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No plans yet — add one on the right.
              </CardContent>
            </Card>
          )}
          <div className="space-y-3">
            {plans.data?.items.map((plan) => (
              <Card key={plan.id}>
                <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
                  <div>
                    <CardTitle className="text-lg">{plan.name}</CardTitle>
                    <CardDescription>
                      {plan.duration_days} days · {formatPrice(plan.price_cents, plan.currency)}
                    </CardDescription>
                  </div>
                  {plan.is_active ? (
                    <Badge variant="success">Active</Badge>
                  ) : (
                    <Badge variant="secondary">Disabled</Badge>
                  )}
                </CardHeader>
                {plan.description && (
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{plan.description}</p>
                  </CardContent>
                )}
                {plan.is_active && (
                  <CardFooter>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => deactivate.mutate(plan.id)}
                      disabled={deactivate.isPending}
                    >
                      Deactivate
                    </Button>
                  </CardFooter>
                )}
              </Card>
            ))}
          </div>
        </section>

        <section>
          <Card>
            <CardHeader>
              <CardTitle>Add a plan</CardTitle>
              <CardDescription>Customers will see active plans only.</CardDescription>
            </CardHeader>
            <form onSubmit={handleCreate}>
              <CardContent className="space-y-3">
                <div className="space-y-1.5">
                  <Label htmlFor="pname">Name</Label>
                  <Input
                    id="pname"
                    required
                    minLength={2}
                    maxLength={120}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pdesc">Description</Label>
                  <Input
                    id="pdesc"
                    maxLength={200}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="pdur">Duration (days)</Label>
                    <Input
                      id="pdur"
                      type="number"
                      min={1}
                      required
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="pprice">Price</Label>
                    <Input
                      id="pprice"
                      type="number"
                      min={0}
                      step="0.01"
                      required
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button type="submit" className="w-full" disabled={create.isPending}>
                  {create.isPending ? 'Creating…' : 'Create plan'}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </section>
      </div>
    </main>
  );
}
