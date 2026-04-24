# --- build stage ---
FROM node:20-alpine AS build

WORKDIR /app

# Pin pnpm explicitly so install is deterministic.
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

# package.json has pnpm.onlyBuiltDependencies — required so the native
# postinstalls for unrs-resolver (Turbopack's Rust resolver), sharp, and
# @tailwindcss/oxide actually run in pnpm 10's non-interactive CI mode.
COPY web/package.json web/pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile \
 && pnpm rebuild || true

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
