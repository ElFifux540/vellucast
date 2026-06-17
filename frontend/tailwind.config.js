/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{vue,js,ts}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "Segoe UI",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      boxShadow: {
        "cta": "0 10px 40px -10px rgba(79, 70, 229, 0.45)",
        "cta-hover": "0 14px 48px -8px rgba(79, 70, 229, 0.55)",
      },
    },
  },
  plugins: [],
};
