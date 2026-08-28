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
import { useAuth } from '@/lib/auth';
import {
  notificationKindLabel,
  notificationVariant,
  useMyNotifications,
} from '@/lib/notifications';

function formatDateTime(value: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

export function NotificationsPage() {
  const { user } = useAuth();
  const { data, isLoading } = useMyNotifications(Boolean(user));

  return (
    <main className="container py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Notifications</p>
          <h1 className="text-3xl font-bold">Inbox</h1>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent messages</CardTitle>
          <CardDescription>
            Payment receipts, check-in confirmations, and renewal reminders.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {isLoading && (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
          {!isLoading && (data?.items.length ?? 0) === 0 && (
            <p className="text-sm text-muted-foreground">
              You have no notifications yet.
            </p>
          )}
          {data?.items.map((n) => (
            <div
              key={n.id}
              className="rounded border p-4 text-sm"
              data-testid="notification-row"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{notificationKindLabel(n.kind)}</Badge>
                  <Badge variant={notificationVariant(n.status)}>
                    {n.status}
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">
                  {formatDateTime(n.created_at)}
                </span>
              </div>
              <p className="mt-2 font-medium">{n.subject}</p>
              <p className="mt-1 whitespace-pre-line text-muted-foreground">
                {n.body}
              </p>
              {n.error && (
                <p className="mt-2 text-xs text-destructive">
                  Send error: {n.error}
                </p>
              )}
              {n.sent_at && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Sent {formatDateTime(n.sent_at)}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="mt-8 flex gap-3">
        <Button asChild variant="link" className="px-0">
          <Link to="/dashboard">← Back to dashboard</Link>
        </Button>
        <Button asChild variant="link" className="px-0">
          <Link to="/">← Back to home</Link>
        </Button>
      </div>
    </main>
  );
}
