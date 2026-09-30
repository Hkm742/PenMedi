# Multi-stage Dockerfile for Vue 3 + PrimeVue Frontend using Bun
FROM oven/bun:1-alpine AS builder

WORKDIR /app

ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}

# Copy dependency specifications
COPY package.json bun.lock* ./

# Install dependencies
RUN bun install --frozen-lockfile || bun install

# Copy application source code
COPY . .

# Build production bundle
RUN bun run build-only

# Runtime stage using lightweight Nginx
FROM nginx:alpine AS runtime

ENV PORT=80 \
	NGINX_ENVSUBST_FILTER="^PORT$"

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
