export const theme = {
  colors: {
    primary: '#1e90ff',
    accent: '#00bcd4',
    background: '#f0f7ff',
    foreground: '#111827',
  },
} as const

export type AppTheme = typeof theme
