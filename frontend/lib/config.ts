/**
 * Runtime API configuration for the Lumint frontend.
 *
 * Resolution order for the HTTP base URL:
 *   1. `process.env.NEXT_PUBLIC_API_URL` (injected at build time by Next.js / Vercel)
 *   2. `http://localhost:8000` in development (when running `next dev` against a local FastAPI)
 *   3. `null` in production when no env var is set — callers should detect this and
 *      skip network calls (go straight to mock data) instead of trying to fetch
 *      `http://localhost:8000` from a public deployment, which is what was producing
 *      the 20+ console errors on the live Vercel site.
 *
 * WebSocket host is derived from the HTTP base URL by stripping the protocol.
 */

const DEFAULT_DEV_API_URL = "http://localhost:8000";

/**
 * The configured API base URL, or `null` if no API is reachable from this environment.
 * Use this to gate network calls: `if (apiBaseUrl()) { fetch(...) } else { useMock() }`.
 */
export function apiBaseUrl(): string | null {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }

  // In the browser, only fall back to localhost if the page itself is on localhost.
  // On a deployed Vercel site, the user is NOT on localhost, so we return null and
  // let the caller short-circuit to mock data instead of spamming CORS/SSL errors.
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0") {
      return DEFAULT_DEV_API_URL;
    }
    return null;
  }

  // SSR / build time: assume local dev so server-rendered fetches still work.
  return DEFAULT_DEV_API_URL;
}

/**
 * Returns the WebSocket origin (protocol + host[:port]) for the configured API.
 * Derives `wss://` from `https://` and `ws://` from `http://`. Returns `null`
 * when no API is configured.
 */
export function wsOrigin(): string | null {
  const base = apiBaseUrl();
  if (!base) return null;
  return base.replace(/^http/i, "ws");
}
