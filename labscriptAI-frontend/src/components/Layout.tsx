import React, { ReactNode } from 'react';
import { Box, Container, AppBar, Toolbar, Typography, Button, useMediaQuery, useTheme } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { FlaskConical, Github } from 'lucide-react';
import StepProgress from './StepProgress';

// Define the steps for the application workflow
const steps = [
  { label: 'Welcome', path: '/' },
  { label: 'Hardware Config', path: '/configure-hardware' },
  { label: 'Define SOP', path: '/define-sop' },
  { label: 'Generate Code', path: '/generate-code' },
  { label: 'Simulation', path: '/simulation-results' }
];

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get active step based on current path
  const activeStep = steps.findIndex(step => step.path === location.pathname);
  
  // Only show step progress if we're past the welcome page and not on standalone pages
  const standalonePages = ['/', '/code-input', '/code-editing', '/dev-tools'];
  const showStepProgress = !standalonePages.includes(location.pathname);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="primary" elevation={0}>
        <Toolbar>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              flexGrow: 1, 
              cursor: 'pointer' 
            }}
            onClick={() => navigate('/')}
          >
            <FlaskConical size={28} />
            <Typography 
              variant="h5" 
              component="div" 
              sx={{ 
                ml: 1.5, 
                fontWeight: 700,
                background: 'linear-gradient(90deg, #FFFFFF 70%, #A78BFA 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              LabScript AI
            </Typography>
          </Box>
          
          {!isMobile && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                color="inherit" 
                onClick={() => navigate('/code-input')}
                sx={{ mx: 1 }}
              >
                Code Input
              </Button>
              <Button 
                color="inherit" 
                href="https://github.com/KRATSZ/LabScript-AI" 
                target="_blank" 
                sx={{ mx: 1 }}
                startIcon={<Github size={20} />}
              >
                GitHub
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>
      
      {showStepProgress && (
        <Box sx={{ bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Container maxWidth="lg" sx={{ py: 1 }}>
            <StepProgress steps={steps} activeStep={activeStep} />
          </Container>
        </Box>
      )}
      
      <Container component="main" maxWidth="lg" sx={{ flexGrow: 1, py: 4 }}>
        {children}
      </Container>
      
      <Box 
        component="footer" 
        sx={{ 
          py: 3, 
          mt: 'auto', 
          backgroundColor: theme.palette.grey[100],
          borderTop: `1px solid ${theme.palette.grey[200]}`,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} LabScript AI - Automating lab protocols with AI
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;