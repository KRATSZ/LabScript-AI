import { createTheme } from '@mui/material/styles';

// Color palette
const colors = {
  primary: {
    main: '#2563EB',
    light: '#60A5FA',
    dark: '#1E40AF',
  },
  secondary: {
    main: '#0D9488',
    light: '#5EEAD4',
    dark: '#0F766E',
  },
  accent: {
    main: '#7C3AED',
    light: '#A78BFA',
    dark: '#5B21B6',
  },
  success: {
    main: '#16A34A',
    light: '#4ADE80',
    dark: '#15803D',
  },
  warning: {
    main: '#FBBF24',
    light: '#FCD34D',
    dark: '#D97706',
  },
  error: {
    main: '#EF4444',
    light: '#FCA5A5',
    dark: '#B91C1C',
  },
  grey: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },
};

const theme = createTheme({
  palette: {
    primary: colors.primary,
    secondary: colors.secondary,
    error: colors.error,
    warning: {
      main: colors.warning.main,
    },
    success: {
      main: colors.success.main,
    },
    background: {
      default: colors.grey[50],
      paper: '#FFFFFF',
    },
    text: {
      primary: colors.grey[900],
      secondary: colors.grey[600],
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      lineHeight: 1.2,
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.2,
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.2,
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.125rem',
      lineHeight: 1.2,
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.2,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
          fontWeight: 500,
        },
        containedPrimary: {
          boxShadow: '0 2px 4px rgba(37, 99, 235, 0.25)',
          '&:hover': {
            boxShadow: '0 4px 8px rgba(37, 99, 235, 0.3)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
          borderRadius: 12,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        rounded: {
          borderRadius: 12,
        },
      },
    },
  },
});

export default theme;