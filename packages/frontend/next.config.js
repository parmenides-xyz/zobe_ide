module.exports = {
  experimental: {
    optimizePackageImports: [ '@mantine/core', '@mantine/hooks' ],
  },
  images: {
    unoptimized: true,
  },
  reactStrictMode: true,
  webpack: ( config ) =>
  {
    config.resolve.fallback = { fs: false, path: false }
    return config
  }
};
