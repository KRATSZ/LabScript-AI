import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent,
  useTheme,
  Container,
  Divider,
  alpha
} from '@mui/material';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';

const MotionBox = motion(Box);
const MotionTypography = motion(Typography);
const MotionButton = motion(Button);

const WelcomePage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  const features = [
    {
      title: 'Lab Protocol Automation',
      description: 'Automatically convert natural language descriptions into precise lab automation protocols.',
      icon: <Lucide.Pipette size={36} />,
      color: theme.palette.primary.main
    },
    {
      title: 'Intelligent Code Generation',
      description: 'Generate valid Python code for Opentrons robots with advanced validation.',
      icon: <Lucide.Code2 size={36} />,
      color: theme.palette.secondary.main
    },
    {
      title: 'AI-Powered SOP Creation',
      description: 'Create detailed Standard Operating Procedures with AI assistance.',
      icon: <Lucide.Brain size={36} />,
      color: theme.palette.info.main
    },
    {
      title: 'Simulation & Validation',
      description: 'Test protocols before running them on physical hardware.',
      icon: <Lucide.FlaskRound size={36} />,
      color: theme.palette.success.main
    }
  ];

  const workflowSteps = [
    {
      title: 'Configure Hardware',
      description: 'Select your Opentrons model, pipettes, and labware arrangement.',
      icon: <Lucide.Settings size={24} />,
      number: '1'
    },
    {
      title: 'Define Procedure',
      description: 'Describe your experiment in natural language or review AI-generated steps.',
      icon: <Lucide.FileText size={24} />,
      number: '2'
    },
    {
      title: 'Generate Protocol',
      description: 'Our AI generates Python code for your Opentrons robot.',
      icon: <Lucide.Code size={24} />,
      number: '3'
    },
    {
      title: 'Simulate Protocol',
      description: 'Test and validate your protocol in a virtual environment.',
      icon: <Lucide.PlayCircle size={24} />,
      number: '4'
    },
    {
      title: 'View Animation',
      description: 'Watch a 3D visualization of your protocol execution.',
      icon: <Lucide.Clapperboard size={24} />,
      number: '5'
    }
  ];

  const handleGetStarted = () => {
    navigate('/configure-hardware');
  };

  useEffect(() => {
    document.title = 'LabScript AI - Lab Automation Made Easy';
  }, []);

  return (
    <Container maxWidth="lg">
      <Grid container spacing={6}>
        {/* Hero Section */}
        <Grid item xs={12}>
          <Paper 
            elevation={0}
            sx={{ 
              background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 60%, ${theme.palette.secondary.light} 100%)`,
              borderRadius: 3,
              overflow: 'hidden',
              position: 'relative',
              py: 8,
              px: 4,
            }}
          >
            <Box sx={{ position: 'relative', zIndex: 2 }}>
              <MotionTypography 
                variant="h1" 
                color="white"
                sx={{ mb: 2, fontWeight: 800 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                Lab Automation
                <br />
                <Box component="span" sx={{ color: theme.palette.secondary.light }}>
                  Powered by AI
                </Box>
              </MotionTypography>
              
              <MotionTypography 
                variant="h5" 
                color="white" 
                sx={{ mb: 4, maxWidth: '600px', opacity: 0.9 }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                Transform natural language descriptions into precise lab automation protocols for different robots.
              </MotionTypography>
              
              <MotionButton
                variant="contained"
                color="secondary"
                size="large"
                onClick={handleGetStarted}
                endIcon={<Lucide.ChevronRight />}
                sx={{ 
                  py: 1.5, 
                  px: 4, 
                  fontWeight: 600, 
                  boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)',
                }}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                Get Started
              </MotionButton>
            </Box>
          </Paper>
        </Grid>

        {/* Features Section */}
        <Grid item xs={12}>
          <Typography 
            variant="h3" 
            align="center" 
            sx={{ 
              mb: 4, 
              fontWeight: 700,
              background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Simplify Your Lab Workflow
          </Typography>
          
          <Grid container spacing={3}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card 
                  sx={{ 
                    height: '100%',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 3
                    }
                  }}
                >
                  <CardContent sx={{ textAlign: 'center', p: 3 }}>
                    <Box sx={{ color: feature.color, mb: 2 }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>
        
        {/* Process Overview */}
        <Grid item xs={12}>
          <Divider sx={{ my: 4 }} />
          <Typography 
            variant="h3" 
            align="center" 
            sx={{ mb: 6, fontWeight: 700 }}
          >
            How It Works
          </Typography>
          
          <Grid container spacing={3}>
            {workflowSteps.map((step, index) => (
              <Grid item xs={12} sm={6} md={2.4} key={index}>
                <Box textAlign="center">
                  <Box
                    sx={{
                      width: 60,
                      height: 60,
                      borderRadius: '50%',
                      background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '1.5rem',
                      fontWeight: 'bold',
                      mx: 'auto',
                      mb: 2
                    }}
                  >
                    {step.number}
                  </Box>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                    {step.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default WelcomePage;