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
        "lotto-bg": "#050510",
        "lotto-surface": "rgba(255,255,255,0.03)",
        "lotto-border": "rgba(255,255,255,0.08)",
        "lotto-blue": "#4f6ef7",
        "lotto-purple": "#8b5cf6",
        "lotto-green": "#10b981",
        "lotto-teal": "#06b6d4",
        "lotto-red": "#f43f5e",
        "lotto-amber": "#f59e0b",
        "lotto-text": "#e8eaf6",
        "lotto-muted": "#6b7280",
        // legacy aliases so old classes still compile
        background: "var(--bg)",
        foreground: "var(--text)",
        "lottery-dark": "#050510",
        "lottery-card": "rgba(255,255,255,0.03)",
        "lottery-blue": "#4f6ef7",
        "lottery-green": "#10b981",
        "lottery-red": "#f43f5e",
        "lottery-card-hover": "rgba(255,255,255,0.06)",
      },
    },
  },
  plugins: [],
};
export default config;
