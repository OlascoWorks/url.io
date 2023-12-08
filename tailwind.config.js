/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./website/**/*.{html,js}"],
  theme: {
    screens: {
      'mobile': { 'max': '420px' },
      'sm': '576px',
      'smd': '768px',
      'md': '960px',
      'lmd': '1024px',
      'lg': '1440px'
    },
    extend: {
      fontFamily: {
        'main': ['Inter', 'Arial', 'sans-serif']
      },
      colors: {
        'primary-blue': "#144EE3",
        'primary-green': "#1EB036",
        'bg': "#181E29",
        'main-bg': "#0B101B",
        'text': "#C9CED6",
        'primary-brown': "#B0901E",
        "border": "#353C4A"
      }
    },
  },
  plugins: [],
}

