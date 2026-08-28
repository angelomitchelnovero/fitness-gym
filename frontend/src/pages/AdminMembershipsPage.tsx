import { Badge } from '@/components/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAdminExpiring, useAdminMemberships, formatDate, daysUntil } from '@/lib/memberships';
import { toApiError } from '@/lib/api';

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

export function AdminMembershipsPage() {
  const all = useAdminMemberships(true);
  const expiring = useAdminExpiring(7, true);

  return (
    <main className="container py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Memberships</h1>
        <p className="mt-1 text-muted-foreground">
          Track active, expiring, and recent memberships.
        </p>
      </div>

      <div className="space-y-8">
        <section>
          <h2 className="mb-4 text-xl font-semibold">Expiring in the next 7 days</h2>
          {expiring.isLoading && (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
          {expiring.isError && (
            <p className="text-sm text-destructive">{toApiError(expiring.error).message}</p>
          )}
          {expiring.data && expiring.data.items.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No memberships are expiring this week.
              </CardContent>
            </Card>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            {expiring.data?.items.map((m) => (
              <Card key={m.id}>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <CardTitle className="text-base">Membership #{m.id}</CardTitle>
                  <Badge variant={statusVariant(m.status)}>{m.status}</Badge>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">Ends {formatDate(m.end_date)}</p>
                  <p className="text-sm text-muted-foreground">
                    {daysUntil(m.end_date)} days remaining
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-semibold">All recent memberships</h2>
          {all.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
          {all.data && all.data.items.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No memberships yet.
              </CardContent>
            </Card>
          )}
          <div className="space-y-2">
            {all.data?.items.map((m) => (
              <Card key={m.id}>
                <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
                  <div>
                    <CardTitle className="text-base">Membership #{m.id}</CardTitle>
                    <CardDescription>
                      Plan #{m.plan_id} · {formatDate(m.start_date)} → {formatDate(m.end_date)}
                    </CardDescription>
                  </div>
                  <Badge variant={statusVariant(m.status)}>{m.status}</Badge>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
