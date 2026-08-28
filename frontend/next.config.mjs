import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Pin the tracing root to this project so stray package-lock.json files
  // elsewhere on the machine can't hijack the standalone output path.
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
