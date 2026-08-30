import { useEffect, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';

import { Badge } from '@/components/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';
import { useMyCard } from '@/lib/checkins';

function secondsUntil(iso: string): number {
  return Math.max(0, Math.round((new Date(iso).getTime() - Date.now()) / 1000));
}

function formatSecs(s: number): string {
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

export function MembershipCard() {
  const { user } = useAuth();
  const card = useMyCard(Boolean(user));
  const [secondsLeft, setSecondsLeft] = useState<number>(0);

  useEffect(() => {
    if (!card.data) return;
    const tick = () => setSecondsLeft(secondsUntil(card.data!.expires_at));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [card.data]);

  if (card.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Membership card</CardTitle>
          <CardDescription>Loading…</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (card.isError || !card.data) {
    return (
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle>Membership card</CardTitle>
            <CardDescription>
              No active membership — purchase a plan to get a QR card.
            </CardDescription>
          </div>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>Membership card</CardTitle>
          <CardDescription>
            Show this QR at the front desk.
          </CardDescription>
        </div>
        <Badge variant={secondsLeft < 30 ? 'destructive' : 'success'}>
          {formatSecs(secondsLeft)}
        </Badge>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-3">
        <div className="rounded-lg border bg-white p-4">
          <QRCodeSVG value={card.data.token} size={192} />
        </div>
        <p className="text-xs text-muted-foreground">
          {card.data.plan_name} · token auto-refreshes
        </p>
      </CardContent>
    </Card>
  );
}