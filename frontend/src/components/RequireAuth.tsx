import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth, type Role } from '@/lib/auth';

interface Props {
  children: ReactNode;
  roles?: Role[];
}

export function RequireAuth({ children, roles }: Props) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <main className="container flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (roles && !roles.includes(user.role)) {
    return (
      <main className="container py-12 text-center">
        <h1 className="text-2xl font-bold">403 — Forbidden</h1>
        <p className="mt-2 text-muted-foreground">
          This area is restricted to {roles.join(', ')} accounts.
        </p>
      </main>
    );
  }

  return <>{children}</>;
}
