/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "**"
      },
      {
        protocol: "https",
        hostname: "**"
      }
    ],
    formats: ["image/avif", "image/webp"]
  },
  experimental: {
    optimizeCss: true
  }
}

module.exports = nextConfig
