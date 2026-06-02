import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0d6efd",
        secondary: "#f9a826",
        muted: "#f7f9fc",
        card: "#ffffff",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(17, 24, 39, 0.06)",
      },
      borderRadius: {
        xl: "16px",
        "2xl": "20px",
      },
    },
  },
  plugins: [],
};
export default config;
