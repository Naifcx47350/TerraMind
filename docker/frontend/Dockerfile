# =============================================================================
# Frontend — multi-stage build (Node builds, nginx serves)
# =============================================================================
# Stage 1 "build": compile React → static files in /dist
# Stage 2 "run": tiny nginx image, copy only /dist (smaller, safer)

FROM node:20-alpine AS build

WORKDIR /app/FrontPage/frontend-react

COPY FrontPage/frontend-react/package.json FrontPage/frontend-react/package-lock.json* ./
RUN npm ci

COPY FrontPage/frontend-react/ ./
# Vite alias @assets → repo-root/assets (see vite.config.js)
COPY assets/ /app/assets/

RUN npm run build

FROM nginx:1.27-alpine

COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/FrontPage/frontend-react/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
