"use client";
import { Info, AlertCircle, RefreshCw, CheckCircle2 } from "lucide-react";
import type { ApiHealthStatus } from "@/hooks/useApiHealth";

interface DemoModeBannerProps {
  status: ApiHealthStatus;
  latency: number | null;
  lastError: string | null;
  onRetry: () => void;
}

/**
 * Banner shown across the dashboard pages whenever the backend is not
 * verifiably online. Three branches:
 *   - "offline"  → API URL is set but the probe failed. Show the URL + the
 *                  last error and a Retry button.
 *   - "unknown"  → No API URL is configured at all (demo mode).
 *   - (online)   → Banner is hidden by the parent layout.
 */
export function DemoModeBanner({
  status,
  latency,
  lastError,
  onRetry,
}: DemoModeBannerProps) {
  if (status === "offline") {
    const apiUrl =
      typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
        ? process.env.NEXT_PUBLIC_API_URL
        : "(not set)";
    return (
      <div
        role="alert"
        className="rounded-lg border border-[var(--critical-border)]/40 bg-[var(--critical-bg)] px-4 py-3 flex flex-col gap-3 text-xs font-sans"
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="h-4 w-4 text-[var(--critical)] shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <strong className="font-semibold text-[var(--critical)]">
                API unreachable
              </strong>
              <span className="text-text-muted">·</span>
              <code className="text-[var(--text-2)] bg-surface-raised px-1.5 py-0.5 rounded text-[11px]">
                {apiUrl}
              </code>
            </div>
            <p className="text-[var(--text-2)]">
              {lastError
                ? `Last error: ${lastError}. Render free tier can take 30–60s to wake on first request.`
                : "The backend is not responding. Render free tier can take 30–60s to wake on first request."}
            </p>
          </div>
          <button
            onClick={onRetry}
            className="flex items-center gap-1 text-[var(--critical)] hover:underline shrink-0"
          >
            <RefreshCw className="h-3 w-3" />
            Retry
          </button>
        </div>
        <div className="pl-7 space-y-2">
          <p className="text-[var(--text-2)]">
            Or paste a different backend URL:
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="https://your-api.com"
              className="flex-1 bg-[var(--surface-2)] border border-[var(--border)] rounded px-2 py-1 text-xs"
              id="manual-api-url"
            />
            <button
              type="button"
              onClick={() => {
                const input = document.getElementById(
                  "manual-api-url",
                ) as HTMLInputElement | null;
                const url = input?.value?.trim();
                if (url) {
                  try {
                    window.localStorage.setItem("lumint_api_url", url);
                  } catch {
                    // localStorage may be unavailable in private mode.
                  }
                  window.location.reload();
                }
              }}
              className="text-xs bg-[var(--accent)] text-white px-3 py-1 rounded"
            >
              Use This URL
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (status === "online") {
    return (
      <div
        role="note"
        className="rounded-lg border border-[var(--safe-border)]/30 bg-[var(--safe-bg)] px-4 py-2.5 flex items-center gap-2 text-xs font-sans"
      >
        <CheckCircle2 className="h-4 w-4 text-[var(--safe)] shrink-0" />
        <span className="text-[var(--text-2)]">
          <strong className="font-semibold">Connected to backend</strong>
          {latency != null ? ` · ${latency}ms` : ""}
        </span>
      </div>
    );
  }

  // "unknown" — no API URL set. Original demo-mode copy.
  return (
    <div
      role="note"
      className="rounded-lg border border-[var(--warn-border)]/30 bg-[var(--warn-bg)] px-4 py-2.5 flex items-center gap-2 text-xs font-sans"
    >
      <Info className="h-4 w-4 text-[var(--warn)] shrink-0" />
      <span className="text-[var(--text-2)]">
        <strong className="font-semibold">Demo deployment</strong>{" "}
        — Only UPI Shield is fully functional. Other modules require a
        backend (future enhancement).
      </span>
    </div>
  );
}

export default DemoModeBanner;
