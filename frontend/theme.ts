/**
 * Law-sector design system — professional, trustworthy, distinctive.
 * Works across web and mobile with responsive scaling.
 */

export const colors = {
  // Primary — Deep professional navy
  primary: '#1B2B48',
  primaryLight: '#2C3E5B',
  primaryDark: '#0F1A2D',
  // Accent — High-end gold
  accent: '#B8860B', // DarkGoldenRod
  accentLight: '#DAA520',
  accentMuted: 'rgba(184, 134, 11, 0.1)',
  // Backgrounds — Clean parchment/white
  bgBody: '#FBFBFB',
  bgCard: '#FFFFFF',
  bgSection: '#F4F7FA',
  bgHeader: '#1B2B48',
  bgFooter: '#0F1A2D',
  // Text
  textPrimary: '#1A1A1A',
  textSecondary: '#4A4A4A',
  textMuted: '#7D7D7D',
  textOnDark: '#FFFFFF',
  textOnPrimary: '#FFFFFF',
  // Semantic
  prosecution: '#8B2635',
  prosecutionBg: 'rgba(139, 38, 53, 0.08)',
  defense: '#1B5E3F',
  defenseBg: 'rgba(27, 94, 63, 0.08)',
  success: '#2E6B4A',
  error: '#B91C1C',
  border: 'rgba(27, 43, 72, 0.1)',
  borderStrong: 'rgba(27, 43, 72, 0.2)',
};

export const spacing = {
  xs: 6,
  sm: 12,
  md: 20,
  lg: 32,
  xl: 48,
  xxl: 64,
};

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
};

export const typography = {
  // Use system fonts that feel legal/professional; web can override with a serif
  fontFamily: 'Georgia, "Times New Roman", serif',
  fontFamilySans: 'system-ui, -apple-system, sans-serif',
  sizes: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 22,
    xxl: 28,
    hero: 34,
  },
  weights: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
};

export const breakpoints = {
  phone: 0,
  tablet: 768,
  desktop: 1024,
  wide: 1280,
};
