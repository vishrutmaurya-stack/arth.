import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F8F7F3",
        surface: "#FFFFFF",
        ink: "#17243A",
        muted: "#5F6A78",
        line: "#EAE7DF",
        sage: {
          DEFAULT: "#477B62",
          deep: "#355E4A",
          soft: "#EAF0EB",
        },
        alert: {
          DEFAULT: "#A3462F",
          soft: "#FAEFEA",
        },
        amber: {
          DEFAULT: "#8A6A2F",
          soft: "#F7F0DE",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(23, 36, 58, 0.04)",
        card: "0 14px 34px -20px rgba(23, 36, 58, 0.28)",
        composer:
          "0 20px 50px -24px rgba(23, 36, 58, 0.30), 0 1px 2px rgba(23, 36, 58, 0.04)",
      },
      keyframes: {
        rise: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { opacity: "0.35", transform: "translateY(0)" },
          "40%": { opacity: "1", transform: "translateY(-3px)" },
        },
      },
      animation: {
        rise: "rise 340ms cubic-bezier(0.22, 1, 0.36, 1) both",
        "dot-bounce": "dot-bounce 1.1s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
