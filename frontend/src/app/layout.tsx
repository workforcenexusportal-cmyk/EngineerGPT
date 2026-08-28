import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";
import { ParticleField } from "@/components/particle-field";

export const metadata: Metadata = {
  title: "EngineerGPT — AI OS for Manufacturing Engineers",
  description:
    "Reduce documentation effort, accelerate engineering analysis, and preserve company knowledge with AI-powered engineering agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* Loaded at runtime (not build time) so builds succeed in locked-down/offline CI. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Rajdhani:wght@500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      {/* THEME: cyberpunk shell; decorative particle layer remains aria-hidden. */}
      <body className="aurora min-h-screen">
        <ParticleField />
        <div className="flex">
          <Sidebar />
          <main className="min-h-screen flex-1 px-5 py-6 md:px-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
