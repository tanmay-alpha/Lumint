import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-base': 'var(--bg-base)',
        'surface': 'var(--surface)',
        'border': 'var(--border)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'accent-blue': 'var(--accent-blue)',
        'accent-teal': 'var(--accent-teal)',
        'risk-critical': 'var(--risk-critical)',
        'risk-high': 'var(--risk-high)',
        'risk-medium': 'var(--risk-medium)',
        'risk-safe': 'var(--risk-safe)',
      },
      fontFamily: {
        display: ['var(--font-display)', 'serif'],
        sans: ['var(--font-sans)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      boxShadow: {
        glass: '0 4px 24px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        glassHover: '0 12px 40px rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.06)',
      }
    },
  },
  plugins: [],
}

export default config
