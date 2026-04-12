import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  turbopack: {
    // Sets the filesystem root for module resolution
    // Use path.join(__dirname) for the current directory or '../' to go up
    root: path.join(__dirname, '../../'), 
  },
};

export default nextConfig;
