# Dockerfile — F03 GAMMA (CYPHER Hybrid)
# Image pré-build avec Chromium + fonts + node_modules.
# Build one-time via docker-build.yml, puis les jobs gamma l'utilisent.
#
# ghcr.io/kioka8877-ux/cypher-gamma:latest

FROM node:20-bookworm

# ── System deps ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    ffmpeg \
    fonts-liberation \
    fonts-noto \
    fonts-urw-base35 \
    && rm -rf /var/lib/apt/lists/*

# ── Chrome path for Remotion ─────────────────────────────────
ENV REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app

# ── Install npm dependencies (cached layer) ──────────────────
COPY package.json ./
RUN npm install --omit=dev

# ── Download Google Fonts (woff2) — one-time, no network at render ──
COPY docker-fonts-dl.js ./
RUN node docker-fonts-dl.js

# ── Copy fonts to public/fonts/ ──────────────────────────────
RUN mkdir -p /app/public/fonts && cp /crusader-fonts/*.woff2 /app/public/fonts/

# ── Verify ───────────────────────────────────────────────────
RUN echo "=== Fonts installed ===" && ls -la /app/public/fonts/
RUN echo "=== Chromium ===" && chromium --version
RUN echo "=== node_modules ===" && ls /app/node_modules/ | head -5
