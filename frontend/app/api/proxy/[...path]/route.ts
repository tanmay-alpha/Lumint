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

const BACKEND = (
  process.env.NEXT_PUBLIC_API_URL || "https://lumint-api.onrender.com"
).replace(/\/+$/, "");

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
  // CORS-related — we add our own
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
  // Always tell the backend who the original request was for.
  const xfwdHost = incoming.get("host");
  if (xfwdHost) out.set("x-forwarded-host", xfwdHost);
  out.set("x-lumint-proxy", "1");
  return out;
}

async function forward(req: NextRequest, params: { path: string[] }) {
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

  const subPath = (params?.path || []).join("/");
  const url = `${BACKEND}/${subPath}${req.nextUrl.search}`;

  let body: BodyInit | undefined = undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      body = await req.arrayBuffer();
    } catch {
      body = undefined;
    }
  }

  try {
    const upstream = await fetch(url, {
      method: req.method,
      headers: buildHeaders(req.headers),
      body,
      // Don't keep-alive — let Node pick the best keep-alive strategy.
      cache: "no-store",
    });

    // Copy response headers, dropping hop-by-hop ones.
    const responseHeaders = new Headers();
    for (const [k, v] of upstream.headers.entries()) {
      if (HOP_BY_HOP.has(k.toLowerCase())) continue;
      // CORS: allow the browser to call this proxy freely.
      if (k.toLowerCase() === "access-control-allow-origin") {
        responseHeaders.set(k, "*");
        continue;
      }
      responseHeaders.set(k, v);
    }
    // Set permissive CORS — the proxy is server-side, so the browser
    // sees Vercel as same-origin and never sends a preflight to us.
    if (!responseHeaders.has("access-control-allow-origin")) {
      responseHeaders.set("access-control-allow-origin", "*");
    }

    const responseBody = await upstream.arrayBuffer();
    return new NextResponse(responseBody, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (e: any) {
    return NextResponse.json(
      { detail: `Upstream unreachable: ${e?.message || String(e)}` },
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
