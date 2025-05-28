import React from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepIcon,
  useTheme,
  alpha
} from '@mui/material';
import { Settings, FileText, Code, Play, Clapperboard } from 'lucide-react';

interface StepProgressProps {
  className?: string;
}

const StepProgress: React.FC<StepProgressProps> = ({ className }) => {
  const theme = useTheme();
  const location = useLocation();

  const steps = [
    { path: '/configure-hardware', label: 'Configure Hardware', icon: <Settings size={20} /> },
    { path: '/define-sop', label: 'Define SOP', icon: <FileText size={20} /> },
    { path: '/generate-code', label: 'Generate Code', icon: <Code size={20} /> },
    { path: '/simulation-results', label: 'Simulate Protocol', icon: <Play size={20} /> },
    { path: '/animation', label: 'View Animation', icon: <Clapperboard size={20} /> },
  ];

  const getActiveStep = () => {
    const currentStepIndex = steps.findIndex(step => step.path === location.pathname);
    return currentStepIndex >= 0 ? currentStepIndex : -1;
  };

  const activeStep = getActiveStep();

  // Don't show progress on welcome page or dev tools
  if (location.pathname === '/' || location.pathname === '/dev-tools') {
    return null;
  }

  return (
    <Box className={className} sx={{ py: 2 }}>
      <Stepper activeStep={activeStep} alternativeLabel>
        {steps.map((step, index) => (
          <Step key={step.path}>
            <StepLabel
              StepIconComponent={() => (
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: index <= activeStep 
                      ? theme.palette.primary.main 
                      : alpha(theme.palette.primary.main, 0.1),
                    color: index <= activeStep 
                      ? theme.palette.primary.contrastText 
                      : theme.palette.primary.main,
                    transition: 'all 0.3s ease',
                  }}
                >
                  {step.icon}
                </Box>
              )}
            >
              {step.label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
};

export default StepProgress;