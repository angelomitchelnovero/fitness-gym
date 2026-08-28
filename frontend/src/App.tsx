import { Link, Route, Routes } from 'react-router-dom';

import { RequireAuth } from '@/components/RequireAuth';
import { Button } from '@/components/ui/button';
import { AdminCheckinsPage } from '@/pages/AdminCheckinsPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';
import { CheckoutPage } from '@/pages/CheckoutPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { PaymentsPage } from '@/pages/PaymentsPage';
import { PlansPage } from '@/pages/PlansPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { AdminPlansPage } from '@/pages/AdminPlansPage';
import { AdminMembershipsPage } from '@/pages/AdminMembershipsPage';

function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted">
      <div className="container flex min-h-screen flex-col items-center justify-center text-center">
        <p className="text-sm font-medium uppercase tracking-widest text-primary">
          FitnessGym
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight sm:text-6xl">
          Train smarter.
          <br />
          Membership made simple.
        </h1>
        <p className="mt-6 max-w-xl text-lg text-muted-foreground">
          A modern gym management platform. View plans, manage your membership,
          and check in with a single tap.
        </p>

        <div className="mt-10 flex gap-3">
          <Button asChild>
            <Link to="/plans">View plans</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/register">Get started</Link>
          </Button>
        </div>

        <footer className="absolute bottom-6 text-xs text-muted-foreground">
          Phase 4 — payments ready
        </footer>
      </div>
    </main>
  );
}

function NotFoundPage() {
  return (
    <main className="container py-16 text-center">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="mt-2 text-muted-foreground">Page not found.</p>
      <div className="mt-6">
        <Button asChild>
          <Link to="/">Back to home</Link>
        </Button>
      </div>
    </main>
  );
}

function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-b bg-card">
      <div className="container flex items-center justify-between py-3">
        <div className="flex items-center gap-4">
          <Link
            to="/admin"
            className="text-sm font-medium hover:underline"
          >
            Dashboard
          </Link>
          <Link to="/admin/plans" className="text-sm font-medium hover:underline">
            Plans
          </Link>
          <Link to="/admin/memberships" className="text-sm font-medium hover:underline">
            Memberships
          </Link>
          <Link to="/admin/checkins" className="text-sm font-medium hover:underline">
            Check-ins
          </Link>
          <Link to="/admin/reports" className="text-sm font-medium hover:underline">
            Reports
          </Link>
        </div>
        <Button asChild variant="ghost" size="sm">
          <Link to="/">Exit admin</Link>
        </Button>
      </div>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/plans" element={<PlansPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={
          <RequireAuth roles={['customer']}>
            <DashboardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/checkout"
        element={
          <RequireAuth roles={['customer']}>
            <CheckoutPage />
          </RequireAuth>
        }
      />
      <Route
        path="/payments"
        element={
          <RequireAuth roles={['customer']}>
            <PaymentsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/notifications"
        element={
          <RequireAuth roles={['customer']}>
            <NotificationsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth roles={['admin']}>
            <AdminLayout>
              <AdminDashboardPage />
            </AdminLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/admin/plans"
        element={
          <RequireAuth roles={['admin']}>
            <AdminLayout>
              <AdminPlansPage />
            </AdminLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/admin/memberships"
        element={
          <RequireAuth roles={['admin']}>
            <AdminLayout>
              <AdminMembershipsPage />
            </AdminLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/admin/checkins"
        element={
          <RequireAuth roles={['admin']}>
            <AdminLayout>
              <AdminCheckinsPage />
            </AdminLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/admin/reports"
        element={
          <RequireAuth roles={['admin']}>
            <AdminLayout>
              <ReportsPage />
            </AdminLayout>
          </RequireAuth>
        }
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
