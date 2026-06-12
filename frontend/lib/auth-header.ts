/**
 * Build a Headers object that includes the bearer token (if configured)
 * merged with any caller-supplied headers.
 *
 * Used by every authenticated fetch in `lib/api*` and `lib/api-client.ts`
 * so the frontend can talk to a backend that has LUMINT_API_KEY set.
 *
 * Behavior:
 *   - If NEXT_PUBLIC_API_KEY is set, adds `Authorization: Bearer <key>`.
 *   - If unset, returns the caller headers unchanged (dev/demo deploys).
 *   - If caller headers is undefined, returns an empty Headers object.
 *
 * The backend's `app/dependencies/auth.py` reads LUMINT_API_KEY (with
 * JWT_SECRET fallback) and returns 401 on missing/invalid Authorization.
 * Probes (/api/health, /healthz, /readyz) are public and ignore this.
 */
export function authHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  if (apiKey && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${apiKey}`);
  }
  return headers;
}