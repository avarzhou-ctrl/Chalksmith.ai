import type { NextConfig } from 'next';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { loadEnvFile } from 'node:process';

// The same two files the backend reads: service configuration, then the Clerk
// instance. Already-set environment variables win, so deployments are unaffected.
for (const name of ['env.local', 'clerk.key.stg']) {
  const localEnvFile = resolve(process.cwd(), '../.env', name);
  if (existsSync(localEnvFile)) {
    loadEnvFile(localEnvFile);
  }
}

const nextConfig: NextConfig = {
  output: 'standalone',
};

export default nextConfig;
