import type { NextConfig } from "next";

/** Where the Python service listens. Override with TERRASIM2_API_URL. */
const apiUrl = process.env.TERRASIM2_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Dev resources (HMR) are served to these hosts as well as localhost.
  allowedDevOrigins: ["127.0.0.1"],
  // The browser talks to /api/* on this origin; Next.js forwards it to the service.
  rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
