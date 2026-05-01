/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#e6f5ef",
          100: "#c3e6d5",
          200: "#91d0b0",
          300: "#57b98a",
          400: "#2ea86d",
          500: "#1A6B4A",   // primary
          600: "#155a3e",
          700: "#104830",
          800: "#0b3621",
          900: "#061f13",
        },
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["'Courier New'", "Courier", "monospace"],
      },
      animation: {
        "spin-slow": "spin 1s linear infinite",
        pulse: "pulse 1.5s ease-in-out infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
      },
      keyframes: {
        fadeIn:  { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        slideUp: { "0%": { opacity: 0, transform: "translateY(12px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};
