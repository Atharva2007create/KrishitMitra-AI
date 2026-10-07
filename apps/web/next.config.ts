import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  reactStrictMode: true,
  experimental: {
    cpus: 1,
    workerThreads: true,
  },
};

export default nextConfig;
