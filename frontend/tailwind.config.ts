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
        canvas:           'var(--canvas)',
        surface:          'var(--surface)',
        'surface-2':      'var(--surface-raised)',
        'border-default': 'var(--border)',
        'border-strong':  'var(--border-strong)',
        'text-primary':   'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted':     'var(--text-muted)',
        accent:           'var(--brand)',
        'accent-dark':    'var(--brand-hover)',
        'accent-subtle':  'var(--brand-subtle)',
        teal:             'var(--intel)',
        'teal-subtle':    'var(--intel-subtle)',
        safe:             'var(--risk-none)',
        'safe-subtle':    'var(--risk-none-bg)',
        warn:             'var(--risk-medium)',
        'warn-subtle':    'var(--risk-medium-bg)',
        danger:           'var(--risk-high)',
        'danger-subtle':  'var(--risk-high-bg)',
        critical:         'var(--risk-critical)',
        'critical-subtle':'var(--risk-critical-bg)',
        'ai-border':      'var(--ai-border)',
        'ai-bg':          'var(--ai-subtle)',
        'ai-text':        'var(--ai-accent)',
        // Legacy aliases
        'bg-base':        'var(--canvas)',
        border:           'var(--border)',
        'accent-blue':    'var(--brand)',
        'accent-teal':    'var(--intel)',
        'risk-critical':  'var(--risk-critical)',
        'risk-high':      'var(--risk-high)',
        'risk-medium':    'var(--risk-medium)',
        'risk-safe':      'var(--risk-none)',
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
