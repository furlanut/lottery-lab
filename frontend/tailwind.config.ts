import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "lotto-bg": "#0c0c1d",
        "lotto-surface": "rgba(255,255,255,0.05)",
        "lotto-border": "rgba(255,255,255,0.12)",
        "lotto-blue": "#4f6ef7",
        "lotto-purple": "#8b5cf6",
        "lotto-green": "#10b981",
        "lotto-teal": "#06b6d4",
        "lotto-red": "#f43f5e",
        "lotto-amber": "#f59e0b",
        "lotto-text": "#e8eaf6",
        "lotto-muted": "#8b92a8",
        // legacy aliases so old classes still compile
        background: "var(--bg)",
        foreground: "var(--text)",
        "lottery-dark": "#0c0c1d",
        "lottery-card": "rgba(255,255,255,0.05)",
        "lottery-blue": "#4f6ef7",
        "lottery-green": "#10b981",
        "lottery-red": "#f43f5e",
        "lottery-card-hover": "rgba(255,255,255,0.08)",
      },
    },
  },
  plugins: [],
};
export default config;
