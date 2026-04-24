# --- build stage ---
FROM node:20-alpine AS build

WORKDIR /app

# Pin pnpm explicitly so install behavior is deterministic.
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

# pnpm-workspace.yaml MUST be present at install time: pnpm 10 reads
# `onlyBuiltDependencies` from it and skips the postinstall script for any
# package not on that list when running non-interactively. Without this,
# unrs-resolver (Turbopack's Rust-based module resolver) and sharp don't get
# their native .node binaries built — and then Turbopack silently fails with
# "Module not found" on every @/ alias at `pnpm build`.
COPY web/package.json web/pnpm-lock.yaml web/pnpm-workspace.yaml ./

# Install, then unconditionally rebuild native packages. The rebuild is
# defense-in-depth against any upstream Docker layer cache that serves a
# previously-built-but-incomplete install: pnpm rebuild reruns postinstall
# scripts regardless of whether the package is already "installed".
RUN pnpm install --frozen-lockfile \
 && pnpm rebuild sharp unrs-resolver @tailwindcss/oxide

COPY web/ ./

ARG NEXT_PUBLIC_API_BASE=""
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

RUN pnpm build

# --- runtime stage (Next standalone output) ---
FROM node:20-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
# API_UPSTREAM is read by next.config.ts rewrites() at server runtime.
# Override via docker-compose's environment: block.
ENV API_UPSTREAM=http://api:8000

COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
