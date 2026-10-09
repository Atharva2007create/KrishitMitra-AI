/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  reactStrictMode: true,
  experimental: {
    cpus: 1,
    workerThreads: true,
  },
};

export default nextConfig;
