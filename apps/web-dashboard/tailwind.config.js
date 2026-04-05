/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // LedgerLite brand palette (Navy, Orange, Blue)
        brand: {
          navy: "#1B2D4B",
          orange: "#E68A2E",
          blue: "#2B6BAE",
          // Maps defaults used in existing components
          50:  "#eff6ff",
          100: "#dbeafe",
          500: "#2B6BAE", // Medium Blue
          600: "#1B2D4B", // Navy
          700: "#0f1a2c", // Dark Navy
          900: "#0a111d",
          accent: "#E68A2E", // Orange
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
    },
  },
  plugins: [],
}
