import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        moneyball: {
          50: "#eef7ff",
          100: "#dcedff",
          200: "#b8d9ff",
          300: "#8cbfff",
          400: "#5a9bff",
          500: "#3b7dfc",
          600: "#2268f0",
          700: "#1b53c9",
          800: "#1d44a0",
          900: "#1c3a85",
        },
      },
    },
  },
  plugins: [],
};

export default config;
