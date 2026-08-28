/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'maria-pink': {
          light: '#e85a8a',
          dark: '#ff6b9d',
        },
        'maria-bg': {
          light: '#f0eeeb',
          dark: '#0d0d12',
        },
        'maria-text': {
          light: '#1a1a1a',
          dark: '#f0f0f0',
        },
        'maria-muted': {
          light: '#6b6b6b',
          dark: '#9a9a9a',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'aura': 'pulse-aura 4s ease-in-out infinite',
        'breathe': 'breathe 6s ease-in-out infinite',
        'dot-pulse': 'dot-pulse 2s ease-in-out infinite',
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [],
};
