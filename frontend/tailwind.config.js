/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        groww: {
          primary: '#00d09c',
          dark: '#121212',
          light: '#f8fafc',
          gray: '#f1f5f9'
        }
      }
    },
  },
  plugins: [],
}
