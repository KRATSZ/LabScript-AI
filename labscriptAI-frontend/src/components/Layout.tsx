import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  useTheme,
  alpha
} from '@mui/material';
import { Home, Settings, Code, Play, Clapperboard, Wrench } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const navigationItems = [
    { path: '/', label: 'Home', icon: <Home size={18} /> },
    { path: '/configure-hardware', label: 'Hardware', icon: <Settings size={18} /> },
    { path: '/define-sop', label: 'SOP', icon: <Code size={18} /> },
    { path: '/generate-code', label: 'Code', icon: <Code size={18} /> },
    { path: '/simulation-results', label: 'Simulate', icon: <Play size={18} /> },
    { path: '/animation', label: 'Animation', icon: <Clapperboard size={18} /> },
    { path: '/dev-tools', label: 'Dev Tools', icon: <Wrench size={18} /> },
  ];

  const isActivePath = (path: string) => {
    return location.pathname === path;
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* App Bar */}
      <AppBar 
        position="sticky" 
        elevation={0}
        sx={{
          backgroundColor: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Container maxWidth="lg">
          <Toolbar sx={{ px: 0 }}>
            {/* Logo */}
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                flexGrow: 1, 
                fontWeight: 700,
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                cursor: 'pointer'
              }}
              onClick={() => navigate('/')}
            >
              LabScript AI
            </Typography>

            {/* Navigation */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              {navigationItems.map((item) => (
                <Button
                  key={item.path}
                  startIcon={item.icon}
                  onClick={() => navigate(item.path)}
                  sx={{
                    color: isActivePath(item.path) 
                      ? theme.palette.primary.main 
                      : theme.palette.text.secondary,
                    backgroundColor: isActivePath(item.path) 
                      ? alpha(theme.palette.primary.main, 0.1) 
                      : 'transparent',
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.08),
                    },
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: isActivePath(item.path) ? 600 : 400,
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ flex: 1, backgroundColor: theme.palette.background.default }}>
        {children}
      </Box>

      {/* Footer */}
      <Box 
        component="footer" 
        sx={{ 
          py: 3, 
          px: 2, 
          backgroundColor: theme.palette.background.paper,
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Container maxWidth="lg">
          <Typography 
            variant="body2" 
            color="text.secondary" 
            align="center"
          >
            © 2024 LabScript AI. Powered by Opentrons AI Protocol Generator.
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;