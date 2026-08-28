import { Link, Route, Routes } from 'react-router-dom';

import { Button } from '@/components/ui/button';

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
            <Link to="/login">Member login</Link>
          </Button>
        </div>

        <footer className="absolute bottom-6 text-xs text-muted-foreground">
          Phase 1 · Foundation ready
        </footer>
      </div>
    </main>
  );
}

function PlansPage() {
  return (
    <main className="container py-16">
      <h1 className="text-3xl font-bold">Membership plans</h1>
      <p className="mt-2 text-muted-foreground">Plans coming in Phase 3.</p>
    </main>
  );
}

function LoginPage() {
  return (
    <main className="container py-16">
      <h1 className="text-3xl font-bold">Member login</h1>
      <p className="mt-2 text-muted-foreground">Auth coming in Phase 2.</p>
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

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/plans" element={<PlansPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
