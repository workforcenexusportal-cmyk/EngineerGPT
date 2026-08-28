import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const isStaticExport = process.env.EXPORT_STATIC === "1";
const githubPagesBasePath = process.env.GITHUB_PAGES_BASE_PATH ?? "/EngineerGPT";

const nextConfig = {
  reactStrictMode: true,
  // Static GitHub Pages is hosted below /EngineerGPT; without this prefix,
  // browsers request /_next/* from the domain root and receive 404s.
  basePath: isStaticExport ? githubPagesBasePath : "",
  assetPrefix: isStaticExport ? `${githubPagesBasePath}/` : undefined,
  trailingSlash: isStaticExport,
  // Standalone by default (Docker/Fly). Set EXPORT_STATIC=1 for static export
  // (GitHub Pages / any static host).
  output: isStaticExport ? "export" : "standalone",
  // Pin the tracing root to this project so stray package-lock.json files
  // elsewhere on the machine can't hijack the standalone output path.
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
