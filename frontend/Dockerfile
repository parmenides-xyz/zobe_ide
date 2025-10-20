# Kurtosis Frontend Dockerfile
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache libc6-compat python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies with increased memory
RUN NODE_OPTIONS="--max-old-space-size=4096" npm ci --legacy-peer-deps

# Copy application code
COPY . .

# Build the Next.js application with increased memory and reduced optimization
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NEXT_TELEMETRY_DISABLED=1
# Build-time env vars for Phala Cloud - these will be replaced at build time
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8001/ws
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
RUN npm run build

# Production image
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Create a non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy public assets
COPY --from=builder /app/public ./public

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Expose port
EXPOSE 3000

# Environment variables for runtime
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_PUBLIC_API_URL="http://backend:8000"

# Start the application
CMD ["node", "server.js"]