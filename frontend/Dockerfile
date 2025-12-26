# ==============================================================================
# TcyberChatbot Frontend Dockerfile
# Multi-stage build for Next.js with standalone output
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Install dependencies
# ------------------------------------------------------------------------------
FROM node:20-alpine AS deps

# Set working directory
WORKDIR /app

# Use Corepack to activate pnpm
RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

# Copy package files
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY frontend/package.json ./frontend/

# Install dependencies
RUN pnpm install --no-frozen-lockfile --filter frontend...

# ------------------------------------------------------------------------------
# Stage 2: Build the application
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@8.12.1 --activate

COPY --from=deps /app ./
COPY . .

ARG NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the frontend
WORKDIR /app/frontend
RUN pnpm run build
WORKDIR /app

# ------------------------------------------------------------------------------
# Stage 3: Production image
# ------------------------------------------------------------------------------
FROM node:20-alpine AS production

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

# Copy built standalone app from builder
COPY --chown=nextjs:nodejs --from=builder /app/frontend/.next/standalone ./
COPY --chown=nextjs:nodejs --from=builder /app/frontend/.next/static ./frontend/.next/static
COPY --chown=nextjs:nodejs --from=builder /app/frontend/public ./frontend/public

USER nextjs

WORKDIR /app/frontend
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
