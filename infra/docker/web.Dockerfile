FROM node:24-slim AS builder
WORKDIR /srv/chalksmith/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./

ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
RUN npm run build

FROM node:24-slim
ENV NODE_ENV=production PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /srv/chalksmith/frontend
COPY --from=builder /srv/chalksmith/frontend/.next/standalone ./
COPY --from=builder /srv/chalksmith/frontend/.next/static ./.next/static
COPY --from=builder /srv/chalksmith/frontend/public ./public
CMD ["node", "server.js"]
