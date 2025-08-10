import React from 'react';
import { Stepper, Step, StepLabel, Typography, Box, useMediaQuery, useTheme } from '@mui/material';
import { useNavigate } from 'react-router-dom';

interface StepItem {
  label: string;
  path: string;
}

interface StepProgressProps {
  steps: StepItem[];
  activeStep: number;
}

const StepProgress: React.FC<StepProgressProps> = ({ steps, activeStep }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();

  const handleStepClick = (path: string, index: number) => {
    // Only allow navigating to previous steps or the current step
    if (index <= activeStep) {
      navigate(path);
    }
  };

  return (
    <Stepper 
      activeStep={activeStep > 0 ? activeStep : 0} 
      alternativeLabel={isMobile}
      sx={{ 
        '& .MuiStepConnector-line': {
          minHeight: '1px',
        },
      }}
    >
      {steps.filter((_, index) => index > 0).map((step, index) => {
        const isClickable = index < activeStep;
        return (
          <Step 
            key={step.label}
            sx={{
              cursor: isClickable ? 'pointer' : 'default',
              '& .MuiStepLabel-root': {
                transition: 'all 0.2s ease-in-out',
                ...(isClickable && {
                  '&:hover': {
                    color: theme.palette.primary.main,
                  }
                })
              }
            }}
            onClick={() => handleStepClick(step.path, index)}
          >
            <StepLabel>
              <Typography 
                variant="body2" 
                color={index === activeStep - 1 ? 'primary' : isClickable ? 'text.primary' : 'text.secondary'}
                sx={{ fontWeight: index === activeStep - 1 ? 600 : 400 }}
              >
                {step.label}
              </Typography>
            </StepLabel>
          </Step>
        );
      })}
    </Stepper>
  );
};

export default StepProgress;