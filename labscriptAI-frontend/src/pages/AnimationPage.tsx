import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Container,
  Grid,
  Card,
  CardContent,
  CircularProgress
} from '@mui/material';
import { PlayCircle, ArrowLeft, Settings } from 'lucide-react';

const AnimationPage: React.FC = () => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/simulation-results');
  };

  const handleConfigureHardware = () => {
    navigate('/configure-hardware');
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowLeft size={20} />}
            onClick={handleBack}
            sx={{ mb: 2 }}
          >
            Back to Simulation Results
          </Button>
          
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Protocol Animation
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Watch a 3D visualization of your protocol execution
          </Typography>
        </Box>

        {/* Animation Placeholder */}
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center', minHeight: 400 }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 300,
              color: 'text.secondary'
            }}
          >
            <PlayCircle size={64} style={{ marginBottom: 16 }} />
            <Typography variant="h5" gutterBottom>
              Animation Coming Soon
            </Typography>
            <Typography variant="body1" align="center" sx={{ mb: 3, maxWidth: 600 }}>
              3D protocol visualization will be available in a future update. 
              This feature will show your robot executing the protocol step by step.
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Settings size={20} />}
              onClick={handleConfigureHardware}
            >
              Configure New Protocol
            </Button>
          </Box>
        </Paper>

        {/* Future Features */}
        <Grid container spacing={3} sx={{ mt: 4 }}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Real-time Visualization
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Watch your protocol execute in real-time with accurate 3D models of your hardware setup.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Interactive Controls
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pause, rewind, and step through your protocol to understand each operation.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Export Options
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Export animations as video files for documentation and training purposes.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default AnimationPage;