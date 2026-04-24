import path from "node:path";
import type { NextConfig } from "next";

/**
 * API proxy — keeps the browser on a single origin in production.
 *
 *  Browser → https://your-host/api/…   (Next.js server rewrite)
 *         → http://api:8000/api/…       (internal Docker network)
 *
 * In local dev, API_UPSTREAM is unset and we fall through to
 * http://localhost:8000, which matches the local uvicorn server.
 *
 * Rewrites pass the response through unbuffered, so SSE event streams work
 * end-to-end without any extra plumbing.
 */
const API_UPSTREAM = process.env.API_UPSTREAM || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",

  // Tell Turbopack the @/ alias explicitly, independent of tsconfig paths.
  // Turbopack has bitten us in Docker builds where it fails to read
  // tsconfig's baseUrl + paths correctly and emits "Module not found" for
  // every @/... import. Making the alias first-class in next.config avoids
  // that path entirely.
  turbopack: {
    resolveAlias: {
      "@": path.resolve(process.cwd(), "."),
    },
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_UPSTREAM}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
