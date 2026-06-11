"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to console in development only — production logs go to Vercel
    if (process.env.NODE_ENV === "development") {
      // eslint-disable-next-line no-console
      console.error("Lumint page error:", error);
    }
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-[var(--canvas)]">
      <div className="max-w-md rounded-lg border border-[var(--high)]/40 bg-[var(--surface-1)] p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-[var(--high)]">
          Something went wrong
        </h2>
        <p className="mt-2 text-sm text-[var(--text-2)]">
          {error.message || "An unexpected error occurred."}
        </p>
        {error.digest && (
          <p className="mt-1 text-xs text-[var(--text-3)] font-mono">
            Error ID: {error.digest}
          </p>
        )}
        <div className="mt-4 flex gap-2">
          <button
            onClick={reset}
            className="rounded-md bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity"
          >
            Try again
          </button>
          <a
            href="/dashboard"
            className="rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-4 py-2 text-sm font-medium text-[var(--text-1)] hover:bg-[var(--surface-3)] transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
