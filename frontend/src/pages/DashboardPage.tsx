import { Link } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/lib/auth';

export function DashboardPage() {
  const { user, logout } = useAuth();

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
        <Card>
          <CardHeader>
            <CardTitle>Membership</CardTitle>
            <CardDescription>Status and expiration.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">Coming in Phase 3.</p>
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
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <Button asChild variant="link" className="px-0">
          <Link to="/">← Back to home</Link>
        </Button>
      </div>
    </main>
  );
}
