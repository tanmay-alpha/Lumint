import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./services/**/*.{js,ts,jsx,tsx,mdx}",
    "./types/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // New Lumint design tokens
        canvas:           'var(--color-canvas)',
        surface:          'var(--color-surface)',
        'surface-2':      'var(--color-surface-2)',
        'border-default': 'var(--color-border)',
        'border-strong':  'var(--color-border-strong)',
        'text-primary':   'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-muted':     'var(--color-text-muted)',
        accent:           'var(--color-accent)',
        'accent-dark':    'var(--color-accent-dark)',
        'accent-subtle':  'var(--color-accent-subtle)',
        teal:             'var(--color-teal)',
        'teal-subtle':    'var(--color-teal-subtle)',
        safe:             'var(--color-safe)',
        'safe-subtle':    'var(--color-safe-subtle)',
        warn:             'var(--color-warn)',
        'warn-subtle':    'var(--color-warn-subtle)',
        danger:           'var(--color-danger)',
        'danger-subtle':  'var(--color-danger-subtle)',
        critical:         'var(--color-critical)',
        'critical-subtle':'var(--color-critical-subtle)',
        'ai-border':      'var(--color-ai-border)',
        'ai-bg':          'var(--color-ai-bg)',
        'ai-text':        'var(--color-ai-text)',
        // Legacy aliases (keep existing components working)
        'bg-base':        'var(--color-canvas)',
        border:           'var(--color-border)',
        'accent-blue':    'var(--color-accent)',
        'accent-teal':    'var(--color-teal)',
        'risk-critical':  'var(--color-danger)',
        'risk-high':      'var(--color-warn)',
        'risk-medium':    '#FFCC00',
        'risk-safe':      'var(--color-safe)',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Georgia', 'serif'],
        sans:    ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono:    ['var(--font-mono)', 'Courier New', 'monospace'],
      },
      fontSize: {
        'display': ['56px', { lineHeight: '1.05', letterSpacing: '-0.02em' }],
        'h1':      ['36px', { lineHeight: '1.15', letterSpacing: '-0.01em' }],
        'h2':      ['24px', { lineHeight: '1.3'  }],
        'h3':      ['18px', { lineHeight: '1.4', fontWeight: '600' }],
        'body':    ['15px', { lineHeight: '1.6'  }],
        'label':   ['13px', { lineHeight: '1.4', fontWeight: '500', letterSpacing: '0.06em' }],
        'mono-lg': ['20px', { lineHeight: '1.3', fontWeight: '500' }],
        'mono-sm': ['14px', { lineHeight: '1.5'  }],
      },
      boxShadow: {
        1:      '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        2:      '0 4px 16px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04)',
        3:      '0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)',
        // Legacy
        glass:      '0 4px 24px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        glassHover: '0 12px 40px rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.06)',
      },
      borderRadius: {
        card: '16px',
      },
      spacing: {
        '4.5': '18px',
        '18':  '72px',
      },
      animation: {
        'shimmer':     'shimmer 1.4s infinite linear',
        'risk-pulse':  'risk-pulse 1.5s ease-in-out 1',
        'float':       'float 3s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0'  },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
}

export default config
