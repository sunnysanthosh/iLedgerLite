/** @type {import('next').NextConfig} */
const nextConfig = {
  // Dashboard pages are fully client-side; no SSR needed for protected routes
  reactStrictMode: true,
}

module.exports = nextConfig
