/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#0B1628',
          primary: '#0474C4',
          'primary-dark': '#036BA3',
          accent: '#4895EF',
          'broken-white': '#F5F5F5',
          secondary: '#112240',
        },
      },
      boxShadow: {
        soft: '0 10px 30px rgba(0, 0, 0, 0.25)',
      },
      fontFamily: {
        oswald: ['var(--font-oswald)', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
