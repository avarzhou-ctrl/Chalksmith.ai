import type { NextConfig } from 'next';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { loadEnvFile } from 'node:process';

const localEnvFile = resolve(process.cwd(), '../.env/.env.frontend.local');
if (existsSync(localEnvFile)) {
  loadEnvFile(localEnvFile);
}

const nextConfig: NextConfig = {
  output: 'standalone',
};

export default nextConfig;
