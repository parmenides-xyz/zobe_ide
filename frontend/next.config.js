module.exports = {
  output: 'standalone',
  experimental: {
    optimizePackageImports: [ '@mantine/core', '@mantine/hooks' ],
  },
  images: {
    unoptimized: true,
  },
  reactStrictMode: true,
  swcMinify: false,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  webpack: ( config, { isServer } ) =>
  {
    config.resolve.fallback = { fs: false, path: false }
    if (!isServer) {
      config.optimization.splitChunks.cacheGroups = {
        default: false,
        vendors: false,
      };
    }
    return config
  }
};
