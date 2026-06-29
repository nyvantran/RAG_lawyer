# Stage 1: Build ứng dụng Next.js
FROM node:20-alpine AS builder

WORKDIR /app

# Sao chép package.json và package-lock.json để tận dụng Docker cache
COPY package*.json ./

# Cài đặt dependencies
RUN npm ci

# Sao chép toàn bộ mã nguồn frontend
COPY . .

# Khai báo build-arg cho API URL (sẽ được nhúng vào frontend lúc build)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build ứng dụng Next.js sang production
RUN npm run build

# Stage 2: Runner - Chạy ứng dụng Next.js trong môi trường production tối giản
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Sao chép các file cần thiết từ stage builder sang stage runner
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Expose port mặc định của Next.js
EXPOSE 3000

# Khởi chạy frontend Next.js ở chế độ production
CMD ["npm", "run", "start"]
