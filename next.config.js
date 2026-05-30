/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In local development, we proxy /api to the FastAPI server on port 8000.
    // On Vercel (production), the /api directory is automatically served 
    // as serverless functions, so no rewrites are needed.
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "/api/index.py",
      },
    ];
  },
};

module.exports = nextConfig;
