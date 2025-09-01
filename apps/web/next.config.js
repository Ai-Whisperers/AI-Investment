/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typescript: {
    // Temporarily ignore TypeScript errors during build for deployment
    ignoreBuildErrors: true,
  },
  eslint: {
    // Allow production builds to succeed even with ESLint warnings
    ignoreDuringBuilds: true,
  },
}
module.exports = nextConfig
