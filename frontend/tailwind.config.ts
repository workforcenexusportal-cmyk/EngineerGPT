import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // THEME: only two saturated accents keep neon coverage restrained.
        base: "#0A0A0F",
        cyan: { DEFAULT: "#00FFF5" },
        magenta: { DEFAULT: "#FF2BD6" },
        // Compatibility aliases: legacy screens resolve to the same two neon accents.
        sky: { DEFAULT: "#00FFF5" },
        violet: { DEFAULT: "#FF2BD6" },
      },
      fontFamily: {
        sans: ["Fira Code", "JetBrains Mono", "ui-monospace", "monospace"],
        display: ["Rajdhani", "Teko", "Impact", "sans-serif"],
      },
      backdropBlur: {
        glass: "24px",
      },
      keyframes: {
        "gradient-move": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
      animation: {
        "gradient-move": "gradient-move 8s ease infinite",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
