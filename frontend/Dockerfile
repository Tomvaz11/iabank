# --- Build Stage ---
FROM node:18-alpine as builder

WORKDIR /app

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install

COPY frontend/ .
RUN pnpm build

# --- Final Stage ---
FROM nginx:1.25-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config if you have one
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]