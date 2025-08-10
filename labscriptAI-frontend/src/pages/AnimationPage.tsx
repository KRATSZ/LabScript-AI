import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  Card, 
  CardContent,
  Grid,
  useTheme,
  Button,
  alpha,
  Stack,
  Paper,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  LinearProgress,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  RotateCcw, 
  Download, 
  Share2, 
  Monitor, 
  Eye, 
  Settings, 
  Fullscreen,
  ChevronDown,
  Clock,
  Activity,
  PlayCircle,
  CheckCircle,
  AlertTriangle,
  FileDown,
  Copy,
  Zap
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useSnackbar } from 'notistack';

const AnimationPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [animationProgress, setAnimationProgress] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [animationLoaded, setAnimationLoaded] = useState(false);
  const [animationDuration, setAnimationDuration] = useState(0);

  // Simulate animation loading and progress
  useEffect(() => {
    const loadTimer = setTimeout(() => {
      setAnimationLoaded(true);
      setAnimationDuration(45); // 45 seconds example duration
    }, 2000);

    return () => clearTimeout(loadTimer);
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && animationProgress < 100) {
      interval = setInterval(() => {
        setAnimationProgress(prev => {
          const newProgress = prev + (100 / animationDuration); // Increment based on duration
          if (newProgress >= 100) {
            setIsPlaying(false);
            return 100;
          }
          return newProgress;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, animationProgress, animationDuration]);

  const handlePlayPause = () => {
    if (!animationLoaded) return;
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setAnimationProgress(0);
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleExport = () => {
    setShowExportDialog(true);
  };

  const handleCopyCode = () => {
    if (state.pythonCode) {
      navigator.clipboard.writeText(state.pythonCode);
      enqueueSnackbar('Protocol code copied to clipboard', { variant: 'success' });
    }
  };

  const getEstimatedTime = () => {
    return Math.round((animationDuration * (100 - animationProgress)) / 100);
  };

  const animationSteps = [
    { label: 'Initialize Robot', completed: animationProgress > 10, time: '0:05' },
    { label: 'Load Pipette Tips', completed: animationProgress > 25, time: '0:12' },
    { label: 'Aspirate Samples', completed: animationProgress > 50, time: '0:28' },
    { label: 'Dispense to Destination', completed: animationProgress > 75, time: '0:35' },
    { label: 'Complete Protocol', completed: animationProgress >= 100, time: '0:45' }
  ];

  useEffect(() => {
    document.title = 'Protocol Animation - LabScript AI';
  }, []);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
        py: 4
      }}
    >
      <Container maxWidth="xl">
        {/* Header Section */}
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <Monitor size={32} color={theme.palette.primary.main} />
            <Typography 
              variant="h3" 
              component="h1" 
              sx={{ 
                fontWeight: 800, 
                ml: 2,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Protocol Animation
            </Typography>
          </Box>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              maxWidth: 800, 
              mx: 'auto',
              lineHeight: 1.6,
              fontWeight: 400,
              mb: 2
            }}
          >
            Watch a detailed visualization of your protocol execution and see exactly how your robot will perform each step
          </Typography>
          
          {state.simulationResults.status && (
            <Stack direction="row" justifyContent="center" spacing={2} sx={{ mt: 2 }}>
              <Chip 
                icon={state.simulationResults.status === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                label={`Simulation: ${state.simulationResults.status.toUpperCase()}`}
                color={state.simulationResults.status === 'success' ? 'success' : 'warning'}
                variant="outlined"
              />
              {state.robotModel && (
                <Chip 
                  label={`Robot: ${state.robotModel}`}
                  color="primary"
                  variant="outlined"
                />
              )}
            </Stack>
          )}
        </Box>

        <Grid container spacing={4}>
          {/* Left Column: Animation Controls and Info */}
          <Grid item xs={12} lg={4}>
            {/* Animation Controls */}
            <Card 
              elevation={0}
              sx={{
                mb: 3,
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                    }}
                  >
                    <PlayCircle size={24} color={theme.palette.primary.main} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Animation Controls
                  </Typography>
                </Stack>

                {!animationLoaded ? (
                  <Box sx={{ textAlign: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Loading animation...
                    </Typography>
                    <LinearProgress 
                      sx={{
                        borderRadius: 1,
                        height: 6,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 1,
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                        }
                      }}
                    />
                  </Box>
                ) : (
                  <>
                    <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
                      <Button
                        variant="contained"
                        onClick={handlePlayPause}
                        startIcon={isPlaying ? <Pause /> : <Play />}
                        sx={{
                          flex: 1,
                          py: 1.5,
                          borderRadius: 2,
                          fontWeight: 600,
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                          '&:hover': {
                            transform: 'translateY(-1px)',
                            boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                          }
                        }}
                      >
                        {isPlaying ? 'Pause' : 'Play'}
                      </Button>
                      
                      <Tooltip title="Reset Animation">
                        <IconButton 
                          onClick={handleReset}
                          sx={{
                            border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                            borderRadius: 2,
                            '&:hover': {
                              background: alpha(theme.palette.primary.main, 0.1),
                              borderColor: theme.palette.primary.main,
                            }
                          }}
                        >
                          <RotateCcw size={20} />
                        </IconButton>
                      </Tooltip>
                      
                      <Tooltip title="Fullscreen">
                        <IconButton 
                          onClick={handleFullscreen}
                          sx={{
                            border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                            borderRadius: 2,
                            '&:hover': {
                              background: alpha(theme.palette.primary.main, 0.1),
                              borderColor: theme.palette.primary.main,
                            }
                          }}
                        >
                          <Fullscreen size={20} />
                        </IconButton>
                      </Tooltip>
                    </Stack>

                    <Box sx={{ mb: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {Math.round(animationProgress)}%
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={animationProgress}
                        sx={{
                          borderRadius: 1,
                          height: 8,
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 1,
                            background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.light})`,
                          }
                        }}
                      />
                    </Box>

                    <Stack spacing={2}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Duration:</Typography>
                        <Chip 
                          icon={<Clock size={16} />}
                          label={`${animationDuration}s`} 
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Remaining:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {getEstimatedTime()}s
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Status:</Typography>
                        <Chip 
                          label={isPlaying ? 'Playing' : animationProgress >= 100 ? 'Completed' : 'Paused'}
                          color={isPlaying ? 'primary' : animationProgress >= 100 ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Stack>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Animation Steps */}
            <Card 
              elevation={0}
              sx={{
                mb: 3,
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                  <Activity size={24} color={theme.palette.info.main} />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Protocol Steps
                  </Typography>
                </Stack>
                
                <List dense sx={{ py: 0 }}>
                  {animationSteps.map((step, index) => (
                    <ListItem key={index} sx={{ px: 0, py: 1 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        {step.completed ? (
                          <CheckCircle size={20} color={theme.palette.success.main} />
                        ) : (
                          <Box
                            sx={{
                              width: 20,
                              height: 20,
                              borderRadius: '50%',
                              border: `2px solid ${theme.palette.grey[300]}`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              color: theme.palette.grey[500],
                            }}
                          >
                            {index + 1}
                          </Box>
                        )}
                      </ListItemIcon>
                      <ListItemText 
                        primary={step.label}
                        secondary={step.time}
                        primaryTypographyProps={{ 
                          variant: 'body2',
                          sx: { 
                            fontWeight: step.completed ? 600 : 400,
                            color: step.completed ? theme.palette.text.primary : theme.palette.text.secondary
                          }
                        }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <Stack spacing={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<ArrowLeft />}
                onClick={() => navigate('/simulation-results')}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  fontWeight: 600,
                  borderColor: alpha(theme.palette.grey[500], 0.3),
                  color: theme.palette.grey[700],
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    borderColor: theme.palette.grey[500],
                    background: alpha(theme.palette.grey[500], 0.05),
                    transform: 'translateY(-1px)',
                  }
                }}
              >
                Back to Simulation Results
              </Button>

              <Button
                fullWidth
                variant="contained"
                startIcon={<Download />}
                onClick={handleExport}
                sx={{
                  py: 1.5,
                  borderRadius: 2,
                  fontWeight: 600,
                  background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                  boxShadow: `0 4px 20px ${alpha(theme.palette.success.main, 0.3)}`,
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 32px ${alpha(theme.palette.success.main, 0.4)}`,
                  }
                }}
              >
                Export Protocol
              </Button>
            </Stack>
          </Grid>

          {/* Right Column: Animation Viewer */}
          <Grid item xs={12} lg={8}>
            <Card 
              elevation={0}
              sx={{
                borderRadius: 3,
                border: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                }
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 3 }}>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                      }}
                    >
                      <Eye size={24} color={theme.palette.primary.main} />
                    </Box>
                    <Box>
                      <Typography variant="h5" sx={{ fontWeight: 700 }}>
                        Protocol Visualization
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Interactive 3D simulation of your protocol execution
                      </Typography>
                    </Box>
                  </Stack>
                  
                  <Tooltip title="Animation Settings">
                    <IconButton 
                      sx={{
                        borderRadius: 2,
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          background: alpha(theme.palette.primary.main, 0.1),
                          transform: 'scale(1.1)',
                        }
                      }}
                    >
                      <Settings size={20} />
                    </IconButton>
                  </Tooltip>
                </Stack>

                {/* Animation Container */}
                <Paper
                  elevation={0}
                  sx={{
                    position: 'relative',
                    height: '600px',
                    borderRadius: 3,
                    border: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    overflow: 'hidden',
                    background: `linear-gradient(135deg, ${alpha(theme.palette.grey[100], 0.5)} 0%, ${alpha(theme.palette.grey[50], 0.8)} 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      border: `2px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                    }
                  }}
                >
                  {!animationLoaded ? (
                    <Box sx={{ textAlign: 'center' }}>
                      <Box
                        sx={{
                          width: 80,
                          height: 80,
                          borderRadius: '50%',
                          background: `conic-gradient(${theme.palette.primary.main}, ${theme.palette.secondary.main}, ${theme.palette.primary.main})`,
                          animation: 'spin 2s linear infinite',
                          mb: 2,
                          '@keyframes spin': {
                            '0%': { transform: 'rotate(0deg)' },
                            '100%': { transform: 'rotate(360deg)' },
                          },
                        }}
                      />
                      <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                        Loading Animation
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Preparing your protocol visualization...
                      </Typography>
                    </Box>
                  ) : (
                    <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
                      {/* Placeholder for actual animation iframe */}
                      <iframe
                        src="about:blank" // Replace with actual animation URL
                        style={{
                          width: '100%',
                          height: '100%',
                          border: 'none',
                          borderRadius: '12px',
                        }}
                        title="Protocol Animation Viewer"
                      />
                      
                      {/* Animation overlay with protocol info */}
                      <Box
                        sx={{
                          position: 'absolute',
                          top: 16,
                          right: 16,
                          background: alpha(theme.palette.background.paper, 0.9),
                          backdropFilter: 'blur(10px)',
                          borderRadius: 2,
                          p: 2,
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                        }}
                      >
                        <Stack spacing={1}>
                          <Typography variant="caption" color="text.secondary">
                            Current Step
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {animationSteps.find(step => !step.completed)?.label || 'Protocol Complete'}
                          </Typography>
                        </Stack>
                      </Box>

                      {/* Progress indicator overlay */}
                      <Box
                        sx={{
                          position: 'absolute',
                          bottom: 16,
                          left: 16,
                          right: 16,
                          background: alpha(theme.palette.background.paper, 0.9),
                          backdropFilter: 'blur(10px)',
                          borderRadius: 2,
                          p: 2,
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            Animation Progress
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {Math.round(animationProgress)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={animationProgress}
                          sx={{
                            borderRadius: 1,
                            height: 6,
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 1,
                              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                            }
                          }}
                        />
                      </Box>
                    </Box>
                  )}
                </Paper>

                {/* Animation Info */}
                {animationLoaded && (
                  <Accordion sx={{ mt: 3 }}>
                    <AccordionSummary expandIcon={<ChevronDown />}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>
                        Protocol Details & Export Options
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                            Animation Information
                          </Typography>
                          <Stack spacing={1}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">Robot Model:</Typography>
                              <Typography variant="body2">{state.robotModel || 'OT-2'}</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">Total Duration:</Typography>
                              <Typography variant="body2">{animationDuration}s</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <Typography variant="body2" color="text.secondary">Protocol Steps:</Typography>
                              <Typography variant="body2">{animationSteps.length}</Typography>
                            </Box>
                          </Stack>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                            Quick Actions
                          </Typography>
                          <Stack spacing={2}>
                            <Button
                              fullWidth
                              variant="outlined"
                              startIcon={<Copy />}
                              onClick={handleCopyCode}
                              size="small"
                            >
                              Copy Protocol Code
                            </Button>
                            <Button
                              fullWidth
                              variant="outlined"
                              startIcon={<Share2 />}
                              size="small"
                            >
                              Share Animation
                            </Button>
                          </Stack>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Export Dialog */}
        <Dialog 
          open={showExportDialog} 
          onClose={() => setShowExportDialog(false)}
          maxWidth="sm"
          fullWidth
          PaperProps={{
            sx: {
              borderRadius: 3,
              boxShadow: `0 24px 48px ${alpha(theme.palette.common.black, 0.12)}`,
            }
          }}
        >
          <DialogTitle sx={{ pb: 2 }}>
            <Stack direction="row" alignItems="center" spacing={2}>
              <FileDown size={24} color={theme.palette.primary.main} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Export Protocol
              </Typography>
            </Stack>
          </DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose how you would like to export your protocol:
            </Typography>
            <Stack spacing={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FileDown />}
                sx={{ justifyContent: 'flex-start', py: 1.5 }}
              >
                Download Python Code (.py)
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Download />}
                sx={{ justifyContent: 'flex-start', py: 1.5 }}
              >
                Export Animation Video (.mp4)
              </Button>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Share2 />}
                sx={{ justifyContent: 'flex-start', py: 1.5 }}
              >
                Generate Shareable Link
              </Button>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setShowExportDialog(false)} variant="outlined">
              Cancel
            </Button>
            <Button variant="contained" startIcon={<Zap />}>
              Export All
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Box>
  );
};

export default AnimationPage;