/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Google Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Semantic CSS variable references
        'cr-bg': 'hsl(var(--color-cr-bg) / <alpha-value>)',
        'cr-bg-soft': 'hsl(var(--color-cr-bg-soft) / <alpha-value>)',
        'cr-surface': 'hsl(var(--color-cr-surface) / <alpha-value>)',
        'cr-surface-variant': 'hsl(var(--color-cr-surface-variant) / <alpha-value>)',
        'cr-text': 'hsl(var(--color-cr-text) / <alpha-value>)',
        'cr-text-dim': 'hsl(var(--color-cr-text-dim) / <alpha-value>)',
        'cr-border': 'hsl(var(--color-cr-border) / <alpha-value>)',
        'cr-outline': 'hsl(var(--color-cr-outline) / <alpha-value>)',

        // Numbered palette for explicit shade references
        cr: {
          950: '#121317',
          900: '#1a1b21',
          850: '#22242c',
          800: '#2c2e38',
          700: '#3d4050',
          600: '#555869',
          500: '#6e7182',
          400: '#8d90a0',
          300: '#b0b3c0',
          200: '#d1d3db',
          100: '#e8e9ed',
          50:  '#f4f5f7',
        },
        // Accent — Google-style purple
        accent: {
          950: '#1a0535',
          900: '#2d0a5e',
          800: '#3d1080',
          700: '#5318a8',
          600: '#6528c7',
          500: '#7c3aed',
          400: '#9b6bf2',
          300: '#b794f6',
          200: '#d4bffa',
          100: '#ede5fc',
          50:  '#f7f3ff',
        },
        // Semantic: success/warn/error
        success: { 500: '#10b981', 400: '#34d399', 300: '#6ee7b7' },
        warn:    { 500: '#f59e0b', 400: '#fbbf24', 300: '#fcd34d' },
        error:   { 500: '#ef4444', 400: '#f87171', 300: '#fca5a5' },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slideUp 0.3s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
