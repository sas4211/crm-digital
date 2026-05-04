/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/api/tickets/:path*",   destination: "http://localhost:8000/tickets/:path*"   },
      { source: "/api/customers/:path*", destination: "http://localhost:8000/customers/:path*" },
      { source: "/api/reports/:path*",   destination: "http://localhost:8000/reports/:path*"   },
      { source: "/api/health",           destination: "http://localhost:8000/health"            },
      { source: "/api/webhooks/:path*",  destination: "http://localhost:8000/webhooks/:path*"  },
    ];
  },
};

module.exports = nextConfig;
