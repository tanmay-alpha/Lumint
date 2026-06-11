import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-[var(--canvas)]">
      <div className="text-center max-w-md">
        <div className="text-6xl font-bold text-[var(--accent)] mb-2">404</div>
        <h1 className="text-xl font-semibold text-[var(--text-1)]">Page not found</h1>
        <p className="mt-2 text-sm text-[var(--text-2)]">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6 flex gap-2 justify-center">
          <Link
            href="/dashboard"
            className="inline-block rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/"
            className="inline-block rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-4 py-2 text-sm font-medium text-[var(--text-1)] hover:bg-[var(--surface-3)] transition-colors"
          >
            Home
          </Link>
        </div>
      </div>
    </div>
  );
}