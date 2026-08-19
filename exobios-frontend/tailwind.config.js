/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          800: '#0f1b35',
          900: '#0a1628',
          950: '#060e1f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            '--tw-prose-body': theme('colors.slate.700'),
            '--tw-prose-headings': theme('colors.navy.900'),
            '--tw-prose-bold': theme('colors.slate.900'),
            '--tw-prose-links': theme('colors.blue.600'),
            '--tw-prose-bullets': theme('colors.slate.300'),
            '--tw-prose-counters': theme('colors.slate.400'),
            '--tw-prose-th-borders': theme('colors.slate.200'),
            '--tw-prose-td-borders': theme('colors.slate.100'),
            maxWidth: 'none',
            fontSize: theme('fontSize.sm')[0],
            lineHeight: '1.6',
            p: { marginTop: '0.6em', marginBottom: '0.6em' },
            'h1, h2, h3, h4': { fontWeight: '600', marginTop: '1em', marginBottom: '0.4em' },
            'ul, ol': { marginTop: '0.5em', marginBottom: '0.5em' },
            li: { marginTop: '0.2em', marginBottom: '0.2em' },
            table: { fontSize: '0.85em' },
            'thead th': { fontWeight: '600', color: theme('colors.slate.700') },
            code: {
              backgroundColor: theme('colors.slate.100'),
              padding: '0.15em 0.4em',
              borderRadius: '0.35em',
              fontWeight: '500',
            },
            'code::before': { content: 'none' },
            'code::after': { content: 'none' },
          },
        },
      }),
    },
  },
  plugins: [require('@tailwindcss/typography')],
}

