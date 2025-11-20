import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Grid, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  CircularProgress,
  Divider, 
  Paper, 
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  alpha,
  Stack,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  ArrowLeft, 
  Play, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  ChevronDown,
  Clock,
  Droplets,
  Scroll,
  AlertOctagon,
  PlayCircle,
  Monitor,
  Zap,
  FileText,
  Bug,
  Eye,
  Activity,
  Download,
  UploadCloud,
  Info
} from 'lucide-react';
import { useSnackbar } from 'notistack';
import { useAppContext } from '../context/AppContext';
import { apiService, formatHardwareConfig } from '../services/api';

const SimulationResultsPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStartTime, setSimulationStartTime] = useState<Date | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  
  useEffect(() => {
    if (state.simulationResults.status === 'idle') {
      handleRunSimulation();
    }
  }, []);
  
  const handleRunSimulation = async () => {
    if (!state.pythonCode) {
      enqueueSnackbar('No code available to simulate', { variant: 'warning' });
      navigate('/generate-code');
      return;
    }

    setIsSimulating(true);
    setSimulationStartTime(new Date());
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ 
      type: 'SET_SIMULATION_RESULTS', 
      payload: {
        status: 'idle',
        message: 'Preparing simulation environment...',
        details: '',
        suggestions: [],
        raw_simulation_output: null,
        warnings_present: false,
      }
    });

    try {
      // Client-side dispatcher: determine which simulation API to call based on robot model
      const isPyLabRobot = state.robotModel === 'PyLabRobot';
      console.log(`Debug - Robot model: ${state.robotModel}, using ${isPyLabRobot ? 'PyLabRobot' : 'Opentrons'} simulation`);

      let response;
      if (isPyLabRobot) {
        // Call PyLabRobot simulation API
        response = await apiService.runPyLabRobotSimulation({
          protocol_code: state.pythonCode
        });
      } else {
        // Call existing Opentrons simulation API
        response = await apiService.runSimulation({
          protocol_code: state.pythonCode
        });
      }
      
      let simStatus: AppState['simulationResults']['status'] = 'idle';
      if (response.success) {
        simStatus = response.warnings_present ? 'warning' : 'success';
      } else {
        simStatus = 'error';
      }

      dispatch({ 
        type: 'SET_SIMULATION_RESULTS', 
        payload: {
          status: simStatus,
          message: response.final_status_message || (response.success ? 'Simulation Completed Successfully' : 'Simulation Failed'),
          details: response.error_message || response.warning_details || (simStatus === 'error' ? 'An unknown error occurred during simulation' : ''),
          suggestions: [], 
          raw_simulation_output: response.raw_simulation_output,
          warnings_present: response.warnings_present,
        }
      });

      enqueueSnackbar(response.final_status_message || (response.success ? 'Simulation Completed Successfully' : 'Simulation Failed'), { 
        variant: simStatus === 'error' ? 'error' : (simStatus === 'warning' ? 'warning' : 'success')
      });

    } catch (error: any) {
      console.error('Simulation error:', error);
      const errorMessage = error.detail?.message || error.message || 'Unknown simulation error';
      dispatch({ 
        type: 'SET_SIMULATION_RESULTS', 
        payload: {
          status: 'error',
          message: 'Simulation Request Failed',
          details: errorMessage,
          suggestions: ['Check network connection', 'Ensure API server is running', 'Verify code syntax'],
          raw_simulation_output: error.detail?.details || "Could not fetch simulation logs.",
          warnings_present: false, 
        }
      });
      enqueueSnackbar(`Simulation Request Failed: ${errorMessage}`, { variant: 'error' });
    } finally {
      setIsSimulating(false);
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };
  
  const handleDownloadProtocol = () => {
    if (!state.pythonCode) {
      enqueueSnackbar('No code available to download', { variant: 'warning' });
      return;
    }
    
    const blob = new Blob([state.pythonCode], { type: 'text/python' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `protocol_${state.robotModel?.toLowerCase() || 'opentrons'}_${new Date().toISOString().slice(0, 10)}.py`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    enqueueSnackbar('Protocol downloaded successfully', { variant: 'success' });
  };
  
  const handleExportForProtocolsIO = async () => {
    if (!state.userGoal || !state.generatedSop || !state.pythonCode) {
      enqueueSnackbar('Not enough data to create an export package. Please complete all previous steps.', { variant: 'error' });
      return;
    }
    
    setIsExporting(true);
    enqueueSnackbar('Generating export package for protocols.io...', { variant: 'info' });

    try {
      const hardwareConfigString = state.rawHardwareConfigText || formatHardwareConfig(state);
      
      const blob = await apiService.exportForProtocolsIO({
        user_goal: state.userGoal,
        hardware_config: hardwareConfigString,
        sop_markdown: state.generatedSop,
        generated_code: state.pythonCode,
      });

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `protocols_io_export_${new Date().toISOString().slice(0, 10)}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      enqueueSnackbar('protocols.io package downloaded successfully!', { variant: 'success' });

    } catch (error: any) {
      console.error('Export for protocols.io failed:', error);
      enqueueSnackbar(`Failed to generate export package: ${error.message}`, { variant: 'error' });
    } finally {
      setIsExporting(false);
    }
  };
  
  const getStatusIcon = () => {
    switch (state.simulationResults.status) {
      case 'success':
        return <CheckCircle size={32} color={theme.palette.success.main} />;
      case 'warning':
        return <AlertTriangle size={32} color={theme.palette.warning.main} />;
      case 'error':
        return <XCircle size={32} color={theme.palette.error.main} />;
      default:
        return <Monitor size={32} color={theme.palette.info.main} />;
    }
  };
  
  const getStatusColor = () => {
    switch (state.simulationResults.status) {
      case 'success':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'error':
        return theme.palette.error.main;
      default:
        return theme.palette.info.main;
    }
  };
  
  const getStatusBgColor = () => {
    switch (state.simulationResults.status) {
      case 'success':
        return alpha(theme.palette.success.light, 0.1);
      case 'warning':
        return alpha(theme.palette.warning.light, 0.1);
      case 'error':
        return alpha(theme.palette.error.light, 0.1);
      default:
        return alpha(theme.palette.info.light, 0.1);
    }
  };

  const getStatusChipVariant = () => {
    switch (state.simulationResults.status) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  const simulationTime = simulationStartTime && !isSimulating 
    ? Math.round((Date.now() - simulationStartTime.getTime()) / 1000) 
    : null;
  
  useEffect(() => {
    document.title = 'Simulation Results - LabScript AI';
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
              Protocol Simulation Results
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
            Review the validation results of your protocol to ensure it will run correctly on your Opentrons robot
          </Typography>
        </Box>
        
        <Grid container spacing={4}>
          {/* Left Column: Status and Controls */}
          <Grid item xs={12} lg={4}>
            {/* Status Overview Card */}
            <Card 
              elevation={0}
              sx={{
                mb: 3,
                borderRadius: 3,
                border: `2px solid ${getStatusColor()}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(getStatusColor(), 0.25)}`,
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: getStatusBgColor(),
                    }}
                  >
                    {getStatusIcon()}
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                      Simulation Status
                    </Typography>
                    <Chip 
                      label={state.simulationResults.status.toUpperCase()} 
                      color={getStatusChipVariant() as any}
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                </Stack>

                {simulationTime && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Simulation Time:
                    </Typography>
                    <Chip 
                      icon={<Clock size={16} />}
                      label={`${simulationTime}s`} 
                      variant="outlined" 
                      size="small"
                    />
                  </Box>
                )}

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Robot Model: {state.robotModel || 'OT-2'}
                </Typography>

                <Divider sx={{ my: 2 }} />

                <Stack spacing={2}>
                  <Button
                    fullWidth
                    variant="outlined"
                    size="large"
                    startIcon={<Play />}
                    onClick={handleRunSimulation}
                    disabled={isSimulating}
                    sx={{
                      py: 1.5,
                      borderRadius: 2,
                      fontWeight: 600,
                      borderColor: alpha(theme.palette.primary.main, 0.3),
                      color: theme.palette.primary.main,
                      transition: 'all 0.3s ease-in-out',
                      '&:hover': {
                        borderColor: theme.palette.primary.main,
                        background: alpha(theme.palette.primary.main, 0.05),
                        transform: 'translateY(-1px)',
                      }
                    }}
                  >
                    {isSimulating ? 'Re-running...' : 'Re-run Simulation'}
                  </Button>

                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={<Download />}
                    onClick={handleDownloadProtocol}
                    disabled={isSimulating || state.simulationResults.status === 'error'}
                    sx={{
                      py: 1.5,
                      borderRadius: 2,
                      fontWeight: 600,
                      background: `linear-gradient(45deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                      boxShadow: `0 4px 20px ${alpha(theme.palette.secondary.main, 0.3)}`,
                      transition: 'all 0.3s ease-in-out',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: `0 8px 32px ${alpha(theme.palette.secondary.main, 0.4)}`,
                      },
                      '&:disabled': {
                        background: theme.palette.action.disabledBackground,
                        transform: 'none',
                        boxShadow: 'none',
                      }
                    }}
                  >
                    Download Protocol
                  </Button>

                  <Tooltip title="Generates a .zip file with instructions for easy uploading to protocols.io">
                    <Button
                      fullWidth
                      variant="contained"
                      color="info"
                      size="large"
                      startIcon={<UploadCloud />}
                      onClick={handleExportForProtocolsIO}
                      disabled={isSimulating || isExporting || state.simulationResults.status === 'error'}
                      sx={{
                        py: 1.5,
                        borderRadius: 2,
                        fontWeight: 600,
                        background: `linear-gradient(45deg, ${theme.palette.info.main}, ${theme.palette.info.dark})`,
                        boxShadow: `0 4px 20px ${alpha(theme.palette.info.main, 0.3)}`,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: `0 8px 32px ${alpha(theme.palette.info.main, 0.4)}`,
                        },
                        '&:disabled': {
                          background: theme.palette.action.disabledBackground,
                          transform: 'none',
                          boxShadow: 'none',
                        }
                      }}
                    >
                      {isExporting ? 'Exporting...' : 'Export for protocols.io'}
                    </Button>
                  </Tooltip>

                  <Button
                    fullWidth
                    variant="outlined"
                    size="large"
                    startIcon={<ArrowLeft />}
                    onClick={() => navigate('/generate-code')}
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
                    Back to Code Editor
                  </Button>
                </Stack>
              </CardContent>
            </Card>

            {/* Workspace Info Card */}
            <Card
              elevation={0}
              sx={{
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.info.light, 0.5)}`,
                mt: 3,
                background: alpha(theme.palette.info.light, 0.15),
              }}
            >
              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                <Stack direction="row" alignItems="center" spacing={2}>
                  <Info size={24} color={theme.palette.info.main} />
                  <Box>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      Share your work!
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Publish your protocol to our{' '}
                      <a 
                        href="https://www.protocols.io/joinworkspace/labscriptai/TDSSYJZRPW" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{ color: theme.palette.info.dark, fontWeight: 'bold' }}
                      >
                        LabscriptAI Workspace
                      </a>
                      {' '}on protocols.io.
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Quick Stats Card */}
            {!isSimulating && state.simulationResults.status !== 'idle' && (
              <Card 
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.info.main, 0.1)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                    <Activity size={24} color={theme.palette.info.main} />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Quick Stats
                    </Typography>
                  </Stack>
                  
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Status:</Typography>
                      <Chip 
                        label={state.simulationResults.status} 
                        color={getStatusChipVariant() as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    {simulationTime && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">Duration:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{simulationTime}s</Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">Warnings:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {state.simulationResults.warnings_present ? 'Yes' : 'None'}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Grid>

          {/* Right Column: Results */}
          <Grid item xs={12} lg={8}>
            {isSimulating ? (
              <Card
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                }}
              >
                <CardContent sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                  <Box sx={{ textAlign: 'center', maxWidth: 500 }}>
                    <Box
                      sx={{
                        p: 3,
                        mb: 3,
                        borderRadius: '50%',
                        background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <CircularProgress size={60} thickness={4} color="primary" />
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                      Running Protocol Simulation
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3, lineHeight: 1.6 }}>
                      We're validating your protocol code against the Opentrons simulation environment. 
                      This process checks for syntax errors, hardware compatibility, and logical flow.
                    </Typography>
                    <LinearProgress 
                      sx={{
                        borderRadius: 1,
                        height: 8,
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 1,
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                        }
                      }}
                    />
                  </Box>
                </CardContent>
              </Card>
            ) : state.simulationResults.status !== 'idle' ? (
              <Card
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `2px solid ${getStatusColor()}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 32px ${alpha(getStatusColor(), 0.15)}`,
                  }
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        background: getStatusBgColor(),
                        mr: 3,
                      }}
                    >
                      {getStatusIcon()}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                        {state.simulationResults.message || 'Simulation Results'}
                      </Typography>
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Typography variant="body1" color="text.secondary">
                          Simulation for {state.robotModel || 'OT-2'} robot
                        </Typography>
                        {simulationTime && (
                          <Chip 
                            icon={<Clock size={16} />}
                            label={`${simulationTime}s`} 
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </Box>
                  </Box>
                  
                  {(state.simulationResults.details || (state.simulationResults.status === 'warning' && state.simulationResults.warnings_present)) && (
                    <Alert 
                      severity={state.simulationResults.status === 'error' ? 'error' : (state.simulationResults.warnings_present ? 'warning' : 'info')}
                      sx={{ 
                        mb: 3,
                        borderRadius: 2,
                        '& .MuiAlert-message': {
                          width: '100%'
                        }
                      }}
                    >
                      <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                        {state.simulationResults.status === 'error' ? 'Error Details:' : (state.simulationResults.warnings_present ? 'Warning Information:' : 'Details:')}
                      </Typography>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 1,
                          bgcolor: alpha(theme.palette.background.paper, 0.5),
                          maxHeight: '150px',
                          overflow: 'auto',
                          mt: 1,
                          fontFamily: 'monospace',
                          fontSize: '0.875rem',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word'
                        }}
                      >
                        {state.simulationResults.details}
                      </Box>
                    </Alert>
                  )}

                  {state.simulationResults.raw_simulation_output && (
                    <Accordion defaultExpanded={state.simulationResults.status === 'error'} sx={{ mb: 3 }}>
                      <AccordionSummary 
                        expandIcon={<ChevronDown />}
                        sx={{
                          borderRadius: 2,
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.primary.main, 0.04),
                          }
                        }}
                      >
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <FileText size={20} color={theme.palette.primary.main} />
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            Detailed Simulation Log
                          </Typography>
                        </Stack>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Paper 
                          variant="outlined"
                          sx={{
                            p: 3,
                            maxHeight: '400px',
                            overflow: 'auto',
                            bgcolor: alpha(theme.palette.grey[50], 0.5),
                            borderColor: alpha(theme.palette.grey[300], 0.5),
                            borderRadius: 2,
                          }}
                        >
                          <Typography 
                            component="pre" 
                            variant="body2" 
                            sx={{ 
                              whiteSpace: 'pre-wrap', 
                              wordBreak: 'break-word',
                              fontFamily: 'monospace',
                              lineHeight: 1.5,
                              margin: 0
                            }}
                          >
                            {state.simulationResults.raw_simulation_output}
                          </Typography>
                        </Paper>
                      </AccordionDetails>
                    </Accordion>
                  )}

                  {state.simulationResults.suggestions && state.simulationResults.suggestions.length > 0 && (
                    <Accordion sx={{ mb: 3 }}>
                      <AccordionSummary 
                        expandIcon={<ChevronDown />}
                        sx={{
                          borderRadius: 2,
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.info.main, 0.04),
                          }
                        }}
                      >
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <Bug size={20} color={theme.palette.info.main} />
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            Troubleshooting Suggestions
                          </Typography>
                        </Stack>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {state.simulationResults.suggestions.map((suggestion, index) => (
                            <ListItem key={index} sx={{ pl: 0 }}>
                              <ListItemIcon sx={{ minWidth: '30px' }}>
                                <AlertOctagon size={18} color={theme.palette.info.main} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={suggestion}
                                primaryTypographyProps={{
                                  variant: 'body2',
                                  sx: { lineHeight: 1.5 }
                                }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  )}

                  {/* Success message for successful simulations */}
                  {state.simulationResults.status === 'success' && !state.simulationResults.warnings_present && (
                    <Alert severity="success" sx={{ borderRadius: 2 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                        🎉 Protocol Validation Successful!
                      </Typography>
                      <Typography variant="body2">
                        Your protocol has passed all validation checks and is ready to run on the Opentrons robot.
                        You can now view the animation to see how your protocol will execute.
                      </Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                }}
              >
                <CardContent sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                  <Box sx={{ textAlign: 'center', maxWidth: 500 }}>
                    <Monitor size={64} color={theme.palette.grey[400]} />
                    <Typography variant="h5" sx={{ fontWeight: 700, mt: 2, mb: 2 }}>
                      No Simulation Results
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                      Run a simulation to validate your protocol code and ensure it will execute correctly on your Opentrons robot.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default SimulationResultsPage;