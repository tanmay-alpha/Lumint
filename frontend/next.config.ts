import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't expose source maps in production builds (Next.js generates them by default).
  productionBrowserSourceMaps: false,
  // Remove the X-Powered-By: Next.js header (Vercel strips it on Vercel deploys; matters for self-host).
  poweredByHeader: false,
  // Defense in depth: keep image domains to self.
  images: { remotePatterns: [] },
};

export default nextConfig;
