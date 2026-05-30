/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In local development, we proxy /api to the FastAPI server on port 8000.
    // On Vercel (production), the /api directory is automatically served 
    // as serverless functions, so no rewrites are needed.
    if (process.env.NODE_ENV === "development") {
      return [
        {
          source: "/api/:path*",
          destination: "http://127.0.0.1:8000/api/:path*",
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
