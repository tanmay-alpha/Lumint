/**
 * Catch-all API proxy that forwards every request to the Render backend.
 *
 * This exists so the browser only ever talks to Vercel (same origin) and
 * the actual cross-origin call to Render happens server-to-server, where
 * CORS doesn't apply. Bypasses the need to keep the backend's CORS
 * allowlist in sync with Vercel preview URLs.
 *
 * The frontend's existing /api/* calls are transparently rewritten by
 * the same-origin `lib/api/client.ts` helpers — we just point them at
 * `/api/proxy/...` instead of the Render URL.
 */
import { NextRequest, NextResponse } from "next/server";

const DEFAULT_BACKEND = "https://lumint-api.onrender.com";

function backendOrigin(): string {
  const configured =
    process.env.LUMINT_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    DEFAULT_BACKEND;
  try {
    const url = new URL(configured);
    if (url.protocol !== "https:" && url.protocol !== "http:") return DEFAULT_BACKEND;
    url.pathname = "";
    url.search = "";
    url.hash = "";
    return url.toString().replace(/\/+$/, "");
  } catch {
    return DEFAULT_BACKEND;
  }
}

const BACKEND = backendOrigin();
const API_KEY = process.env.LUMINT_API_KEY?.trim();

// Methods we forward (anything else is rejected).
const ALLOWED_METHODS = new Set([
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "OPTIONS",
  "HEAD",
]);

// Strip headers that should not cross a server-to-server boundary.
const HOP_BY_HOP = new Set([
  "host",
  "connection",
  "content-length",
  "transfer-encoding",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "upgrade",
  "cookie",
  "x-api-key",
  // CORS-related — this same-origin proxy does not forward browser origins.
  "origin",
  "referer",
  "sec-fetch-mode",
  "sec-fetch-site",
  "sec-fetch-dest",
]);

function buildHeaders(incoming: Headers): Headers {
  const out = new Headers();
  for (const [k, v] of incoming.entries()) {
    if (HOP_BY_HOP.has(k.toLowerCase())) continue;
    out.set(k, v);
  }
  // Ask the backend for a plain (uncompressed) response. We handle
  // decompression ourselves so the browser sees an exact `Content-Length`
  // and decodes the body with the right encoding header. Without this,
  // the backend sends `Content-Encoding: gzip` but Vercel's edge has
  // already stripped it, and the browser sees a mismatch and throws
  // ERR_CONTENT_DECODING_FAILED.
  out.set("accept-encoding", "identity");
  // Always tell the backend who the original request was for.
  const xfwdHost = incoming.get("host");
  if (xfwdHost) out.set("x-forwarded-host", xfwdHost);
  if (API_KEY) out.set("x-api-key", API_KEY);
  out.set("x-lumint-proxy", "1");
  return out;
}

async function forward(
  req: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  // Pre-flight from the browser: just return 204 with the right headers.
  if (req.method === "OPTIONS") {
    return new NextResponse(null, { status: 204 });
  }

  if (!ALLOWED_METHODS.has(req.method)) {
    return NextResponse.json(
      { detail: `Method ${req.method} not allowed` },
      { status: 405 },
    );
  }

  // Note: the backend now uses Bearer-token auth from the browser
  // (NEXT_PUBLIC_API_KEY) so the proxy no longer needs to attach an
  // X-Api-Key header. We keep reading LUMINT_API_KEY (server-only) in
  // case the operator wants to inject one for backend ↔ Render auth.

  // Whitelist the prefixes we proxy. This is a closed allowlist so a
  // malicious caller can't use the proxy to reach other backends.
  const { path } = await context.params;
  const subPath = (path || []).join("/");
  // Whitelist of exact subPath matches and prefix roots. The previous
  // version had ``"health"`` here, which never matched the actual
  // segment ``"healthz"`` — so the Vercel proxy returned 404 for any
  // health probe even though the backend worked fine. Add each probe
  // as its own root entry. Same for ``readyz``.
  const allowedRoots = [
    "api",
    "healthz",
    "readyz",
    "docs",
    "openapi.json",
    "redoc",
  ];
  const allowedPrefixes = allowedRoots;
  const hasUnsafeSegment = (path || []).some(
    (segment) => segment === "." || segment === ".." || segment.includes("/") || segment.includes("\\") || segment.includes("\0"),
  );
  const isAllowed =
    !hasUnsafeSegment &&
    allowedPrefixes.some((p) => subPath === p || subPath.startsWith(`${p}/`));
  if (!isAllowed) {
    return NextResponse.json(
      { detail: `Path '/${subPath}' is not proxied` },
      { status: 404 },
    );
  }

  const safePath = (path || []).map((segment) => encodeURIComponent(segment)).join("/");
  const targetUrl = new URL(`/${safePath}`, BACKEND);
  targetUrl.search = req.nextUrl.search;

  let body: BodyInit | undefined = undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      body = await req.arrayBuffer();
    } catch {
      body = undefined;
    }
  }

  try {
    const upstream = await fetch(targetUrl, {
      method: req.method,
      headers: buildHeaders(req.headers),
      body,
      // Don't keep-alive — let Node pick the best keep-alive strategy.
      cache: "no-store",
    });

    // Copy response headers, dropping hop-by-hop ones.
    const responseHeaders = new Headers();
    for (const [k, v] of upstream.headers.entries()) {
      const lk = k.toLowerCase();
      if (HOP_BY_HOP.has(lk)) continue;
      // Strip any compression header — we asked for `identity` and will
      // not re-encode. If the backend ignores accept-encoding, this
      // prevents the browser from trying to double-decompress.
      if (lk === "content-encoding") continue;
      // CORS is intentionally omitted: callers use this route as same-origin,
      // and upstream CORS policy should not be reflected by the proxy.
      if (lk.startsWith("access-control-")) continue;
      responseHeaders.set(k, v);
    }

    const responseBody = await upstream.arrayBuffer();
    return new NextResponse(responseBody, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (e: unknown) {
    console.error("API proxy upstream request failed:", e);
    return NextResponse.json(
      { detail: "Upstream service is unreachable." },
      { status: 502 },
    );
  }
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
export const HEAD = forward;
export const OPTIONS = forward;

// Explicit param marker for the route compiler
export const dynamicParams = true;
export const revalidate = 0;
