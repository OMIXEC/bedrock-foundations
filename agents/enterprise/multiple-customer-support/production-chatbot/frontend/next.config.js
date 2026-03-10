/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Replace with your WebSocket API URL
  env: {
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://your-api-id.execute-api.us-east-1.amazonaws.com/dev',
  },
}

module.exports = nextConfig
