import type { Config } from "tailwindcss";

// Brand palette matches website-official for visual continuity across NeurixAI properties.
const config: Config = {
  content: ["./src/app/**/*.{js,ts,jsx,tsx}", "./src/components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#050B1F",
          dark: "#0A1628",
          blue: "#1A6FFF",
          cyan: "#00B4FF",
          purple: "#7B2FBE",
          violet: "#9D4EDD",
          glow: "#2B7FFF",
        },
      },
      fontFamily: {
        sans: ["Inter", "Noto Sans Thai", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
