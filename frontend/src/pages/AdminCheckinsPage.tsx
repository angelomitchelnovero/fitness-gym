import { useState } from 'react';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { toApiError } from '@/lib/api';
import { formatDate } from '@/lib/memberships';
import { useAdminCheckins, useScan } from '@/lib/checkins';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export function AdminCheckinsPage() {
  const [date, setDate] = useState<string>(todayIso());
  const checkins = useAdminCheckins(date);
  const scan = useScan();

  const [token, setToken] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onScan = () => {
    if (!token.trim()) return;
    setError(null);
    setResult(null);
    scan.mutate(
      { token: token.trim(), source: 'manual' },
      {
        onSuccess: (r) =>
          setResult(`Admitted user #${r.user_id} (check-in #${r.check_in_id})`),
        onError: (e) => setError(toApiError(e).message),
      },
    );
  };

  const items = checkins.data?.items ?? [];

  return (
    <main className="container py-12">
      <div className="mb-8">
        <p className="text-sm text-muted-foreground">Front desk</p>
        <h1 className="text-3xl font-bold">Check-ins</h1>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scan</CardTitle>
            <CardDescription>
              Paste a scanned QR token (use the customer's membership card).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="eyJhbGciOi..."
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <Button
              onClick={onScan}
              disabled={!token.trim() || scan.isPending}
            >
              {scan.isPending ? 'Verifying…' : 'Verify & admit'}
            </Button>
            {result && (
              <p className="text-sm text-green-600">{result}</p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between gap-4 space-y-0">
            <div>
              <CardTitle>Today's check-ins</CardTitle>
              <CardDescription>{items.length} events</CardDescription>
            </div>
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-auto"
            />
          </CardHeader>
          <CardContent className="space-y-2">
            {checkins.isLoading && (
              <p className="text-sm text-muted-foreground">Loading…</p>
            )}
            {!checkins.isLoading && items.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No check-ins for this day.
              </p>
            )}
            {items.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded border px-3 py-2 text-sm"
              >
                <div>
                  <p className="font-medium">User #{c.user_id}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(c.scanned_at)} · {c.source}
                  </p>
                </div>
                <Badge variant={c.accepted ? 'success' : 'destructive'}>
                  {c.accepted ? 'admitted' : c.reason || 'denied'}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}