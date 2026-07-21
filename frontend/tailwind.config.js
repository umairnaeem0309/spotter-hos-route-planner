/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Professional navy / teal / neutral system (no Spotter branding).
        navy: {
          50: "#eef2f7",
          100: "#d6e0ec",
          600: "#1f3a5f",
          700: "#182f4d",
          800: "#12233a",
          900: "#0d1a2b",
        },
        teal: {
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
