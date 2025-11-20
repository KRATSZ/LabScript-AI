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

// Components
import FeatureCard from '../components/welcome/FeatureCard';

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
      color: theme.palette.primary.main,
    },
    {
      title: 'AI Code Editor & Iterator',
      description: 'Edit and refine existing protocol code with conversational AI assistance.',
      icon: <Lucide.Edit3 size={36} />,
      color: theme.palette.warning.main,
    },
    {
      title: 'AI-Powered SOP Creation',
      description: 'Create detailed Standard Operating Procedures with AI assistance.',
      icon: <Lucide.Brain size={36} />,
      color: theme.palette.info.main,
    },
    {
      title: 'Simulation & Validation',
      description: 'Test protocols before running them on physical hardware.',
      icon: <Lucide.FlaskRound size={36} />,
      color: theme.palette.success.main,
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
                Transform natural language descriptions into precise lab automation protocols for differnet robots.
              </MotionTypography>
              
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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
                  whileHover={{ 
                    scale: 1.05,
                    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.25)',
                  }}
                >
                  Get Started
                </MotionButton>
                <MotionButton
                  variant="outlined"
                  color="info"
                  size="large"
                  onClick={() => navigate('/code-editing')}
                  startIcon={<Lucide.Edit />}
                  sx={{
                    py: 1.5,
                    px: 4,
                    fontWeight: 600,
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      backgroundColor: 'rgba(255, 255, 255, 0.1)'
                    }
                  }}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.5 }}
                >
                  Quick Edit
                </MotionButton>
              </Box>
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
          
          <Grid container spacing={3} justifyContent="center">
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <FeatureCard 
                  title={feature.title}
                  description={feature.description}
                  icon={feature.icon}
                  color={feature.color}
                  delay={index * 0.1}
                />
              </Grid>
            ))}
          </Grid>
        </Grid>
        
        {/* Process Overview */}
        <Grid item xs={12}>
          <Divider sx={{ my: 4 }} />
          <Typography variant="h4" align="center" sx={{ mb: 4, fontWeight: 600 }}>
            How It Works
          </Typography>
          
          <Grid container spacing={3}>
            {workflowSteps.map((step, index) => (
              <Grid item xs={12} key={index}>
                <Card 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    position: 'relative',
                    overflow: 'visible',
                    boxShadow: 3,
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-8px)',
                      boxShadow: 6,
                      '& .step-icon': {
                        transform: 'scale(1.1)',
                        backgroundColor: theme.palette.primary.main,
                      }
                    }
                  }}
                >
                  <Box 
                    sx={{ 
                      position: 'absolute',
                      top: -20,
                      left: 20,
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      backgroundColor: theme.palette.primary.main,
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      boxShadow: 2,
                      zIndex: 1,
                    }}
                  >
                    <Typography variant="h6" color="white" fontWeight="bold">
                      {step.number}
                    </Typography>
                  </Box>
                  
                  <Box 
                    className="step-icon"
                    sx={{ 
                      width: 80,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.3s ease-in-out',
                      color: theme.palette.primary.main
                    }}
                  >
                    {step.icon}
                  </Box>
                  
                  <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      {step.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {step.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Grid>
        
        {/* CTA Section */}
        <Grid item xs={12}>
          <Box 
            sx={{ 
              textAlign: 'center', 
              mt: 6, 
              p: 4, 
              backgroundColor: alpha(theme.palette.primary.main, 0.05),
              borderRadius: 3,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            }}
          >
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
              Ready to automate your lab protocols?
            </Typography>
            <Typography variant="body1" paragraph sx={{ maxWidth: 700, mx: 'auto', mb: 4 }}>
              LabScript AI helps you convert complex lab procedures into Opentrons protocols without writing a single line of code.
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button 
              variant="contained" 
              color="primary" 
              size="large" 
              onClick={handleGetStarted}
              endIcon={<Lucide.ArrowRight />}
              sx={{ 
                py: 1.5, 
                px: 4, 
                fontWeight: 600,
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 20px rgba(37, 99, 235, 0.25)',
                }
              }}
            >
              Start Your First Protocol
            </Button>
              
              <Button 
                variant="outlined" 
                color="warning" 
                size="large" 
                onClick={() => navigate('/code-editing')}
                startIcon={<Lucide.Edit3 />}
                sx={{ 
                  py: 1.5, 
                  px: 4, 
                  fontWeight: 600,
                  borderWidth: 2,
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    borderWidth: 2,
                    boxShadow: '0 6px 20px rgba(251, 146, 60, 0.25)',
                  }
                }}
              >
                Edit Existing Code
              </Button>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default WelcomePage;