# BD Intelligence Dashboard - Docker Image
# Phase 20A — Multi-stage build: build with Node, serve with nginx

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

COPY . .

# Build for production (API_BASE is empty — nginx proxies to hub_api)
ENV VITE_API_BASE=
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config to proxy API requests to hub_api
RUN cat > /etc/nginx/conf.d/default.conf << 'NGINX'
server {
    listen 3000;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to hub_api service
    location ~ ^/(api|health|stats|search|ask|agents|memory|bdgraph|cache|qa|pipeline|alerts|rag|agent|dify|collections|contacts|programs|jobs|ingest|sync|index|dashboard|documents|activities|analytics|ai|graph|notifications|webhooks|contracts|competitive|reports|ml|integrations|outreach|ws|sse|realtime|embeddings|automation|platform)(/|$) {
        proxy_pass http://hub_api:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
}
NGINX

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
