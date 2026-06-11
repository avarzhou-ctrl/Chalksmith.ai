import type { NextConfig } from 'next';
import path from 'path';

const requiredEnvVars = [
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
] as const;

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(
      `Missing required frontend environment variable: ${envVar}. Add it in Vercel Project Settings > Environment Variables and redeploy.`
    );
  }
}

const nextConfig: NextConfig = {
  turbopack: {
    // Sets the filesystem root for module resolution
    // Use path.join(__dirname) for the current directory or '../' to go up
    root: path.join(__dirname, '../../'), 
  },
  async rewrites() {
    const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/static/:path*',
        destination: `${API_BASE_URL}/static/:path*`,
      },
    ];
  },
};

export default nextConfig;
