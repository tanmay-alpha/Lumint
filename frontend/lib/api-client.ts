import {
  StatsResponse,
  RecentEventsResponse,
  CampaignsResponse,
  GraphResponse,
  ThreatSummaryResponse,
  RecentEvent
} from "@/types";
import { apiBaseUrl } from "./config";

// State to track if we are in live or mock mode
export let isLiveMode = false;
let modeListeners: ((live: boolean) => void)[] = [];

export function subscribeToModeChange(listener: (live: boolean) => void) {
  modeListeners.push(listener);
  listener(isLiveMode);
  return () => {
    modeListeners = modeListeners.filter(l => l !== listener);
  };
}

function setLiveMode(live: boolean) {
  if (isLiveMode !== live) {
    isLiveMode = live;
    modeListeners.forEach(listener => listener(live));
  }
}

/**
 * The single network entry point for all Lumint dashboard API calls.
 *
 * Timeouts:
 *   - 30 seconds for file uploads (OCR + ELA + ML takes 5-10s in production,
 *     sometimes longer for large images). A 3-second timeout was the root
 *     cause of the mock-fallback bug: real analysis was always timing out
 *     and the user saw fake `₹1,500 / score 87` data instead.
 *   - 10 seconds for normal JSON endpoints.
 *
 * No mock fallback. If the backend is unreachable, the real error is
 * thrown to the caller so the UI can show a meaningful message.
 */
export async function apiRequest<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    throw {
      message: "Backend not configured. Set NEXT_PUBLIC_API_URL to your FastAPI host.",
      status: 0,
      path,
      isNetworkError: true,
    };
  }
  const url = `${base}${path}`;

  // Inject authorization header if API key is configured.
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const headers = new Headers(options?.headers);
  if (apiKey) {
    headers.set("Authorization", `Bearer ${apiKey}`);
  }

  // Dynamic timeout: uploads need 30s, normal calls 10s.
  const isUpload = options?.body instanceof FormData;
  const timeoutMs = isUpload ? 30000 : 10000;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  // Composite signal: caller signal (for unmount cancellation) + timeout.
  const callerSignal = options?.signal;
  const signal = callerSignal
    ? AbortSignal.any([callerSignal, controller.signal])
    : controller.signal;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal,
    });

    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson && errJson.detail) {
          if (typeof errJson.detail === "string") {
            errorMessage = errJson.detail;
          } else if (Array.isArray(errJson.detail)) {
            errorMessage = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
          }
        }
      } catch (_) {}
      const errorObj: any = new Error(errorMessage);
      errorObj.status = response.status;
      errorObj.path = path;
      throw errorObj;
    }

    setLiveMode(true);
    return (await response.json()) as T;
  } catch (error: any) {
    setLiveMode(false);
    console.error(`[Lumint API] ${options?.method || "GET"} ${path} failed:`, error);

    // Propagate the real error — no mock fallback.
    throw {
      message: error?.message || "Backend unavailable",
      status: error?.status || 0,
      path,
      isNetworkError: !error?.status,
    };
  } finally {
    clearTimeout(timeoutId);
  }
}
