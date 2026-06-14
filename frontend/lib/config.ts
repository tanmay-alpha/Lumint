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
const FALLBACK_API_URL = "https://lumint-api.onrender.com";

/**
 * On a deployed Vercel site, the browser should talk to a same-origin
 * Next.js API route (a transparent proxy) instead of making cross-origin
 * calls to Render. This avoids the CORS preflight and any CSP/connect-src
 * issues — see `app/api/proxy/[...path]/route.ts`.
 *
 * Set `NEXT_PUBLIC_DISABLE_PROXY=1` in the Vercel project env vars to
 * bypass the proxy and call Render directly (useful for debugging CORS).
 */
function shouldUseProxy(): boolean {
  if (typeof window === "undefined") return false;
  if (process.env.NEXT_PUBLIC_DISABLE_PROXY === "1") return false;
  // Only use the proxy on non-localhost hosts (deployed Vercel site).
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0") {
    return false;
  }
  return true;
}

/**
 * The configured API base URL, or `null` if no API is reachable from this environment.
 * Use this to gate network calls: `if (apiBaseUrl()) { fetch(...) } else { useMock() }`.
 */
export function apiBaseUrl(): string | null {
  // Priority: manual override (localStorage) > env var > hardcoded fallback > localhost (dev only)
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem("lumint_api_url");
      if (stored && stored.trim().length > 0) {
        return stored.replace(/\/+$/, "");
      }
    } catch {
      // localStorage may throw in private mode or restricted contexts — ignore.
    }
  }

  // On a deployed Vercel site, use a same-origin proxy. This avoids
  // CORS preflight and any CSP/connect-src issues. See
  // app/api/proxy/[...path]/route.ts.
  if (shouldUseProxy()) {
    return "/api/proxy";
  }

  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }

  // If the env var is missing on a deployed site, fall back to the known
  // Render backend so the frontend still works. This is a hardcoded safety net
  // — operators can override it by setting NEXT_PUBLIC_API_URL in Vercel.
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1" && host !== "0.0.0.0") {
      return FALLBACK_API_URL;
    }
    return DEFAULT_DEV_API_URL;
  }

  // SSR / build time: prefer the fallback so server-rendered fetches hit the
  // real backend instead of localhost.
  return FALLBACK_API_URL;
}

/**
 * Returns the WebSocket origin (protocol + host[:port]) for the configured API.
 * Derives `wss://` from `https://` and `ws://` from `http://`. Returns `null`
 * when no API is configured.
 *
 * Note: the same-origin proxy at `/api/proxy` does NOT forward WebSockets,
 * so on a deployed Vercel site we still need to talk to Render directly
 * for the threat stream. The browser's CSP must allow `wss://*.onrender.com`
 * for this to work.
 */
export function wsOrigin(): string | null {
  // WebSockets always go direct to the backend, even on a deployed site
  // (the proxy is HTTP-only).
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem("lumint_api_url");
      if (stored && stored.trim().length > 0) {
        return stored.replace(/\/+$/, "").replace(/^http/i, "ws");
      }
    } catch {
      // ignore
    }
  }

  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) {
    return fromEnv.replace(/\/+$/, "").replace(/^http/i, "ws");
  }

  return FALLBACK_API_URL.replace(/\/+$/, "").replace(/^http/i, "ws");
}
