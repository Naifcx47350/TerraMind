# =============================================================================
# Frontend — multi-stage build (Node builds, nginx serves)
# =============================================================================
# Stage 1 "build": compile React → static files in /dist
# Stage 2 "run": tiny nginx image, copy only /dist (smaller, safer)

FROM node:20-alpine AS build

WORKDIR /app/web/frontend-react

COPY web/frontend-react/package.json web/frontend-react/package-lock.json* ./
RUN npm ci

COPY web/frontend-react/ ./
# Vite alias @assets -> repo-root/assets (see vite.config.js)
COPY assets/ /app/assets/

RUN npm run build

FROM nginx:1.27-alpine

COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/web/frontend-react/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
