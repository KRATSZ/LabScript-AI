import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  Container,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { ChevronRight, ArrowLeft, Play, ExpandMore, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { useSnackbar } from 'notistack';

const SimulationResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [simulationData, setSimulationData] = useState<any>(null);

  const handleBack = () => {
    navigate('/generate-code');
  };

  const handleViewAnimation = () => {
    navigate('/animation');
  };

  const handleBackToCodeEdit = () => {
    navigate('/generate-code');
  };

  const runSimulation = async () => {
    if (!state.pythonCode.trim()) {
      enqueueSnackbar('No code available to simulate', { variant: 'warning' });
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.simulateProtocol({
        protocol_code: state.pythonCode
      });

      setSimulationData(response);
      
      // Update app state with simulation results
      const status = response.success 
        ? (response.warnings_present ? 'warning' : 'success')
        : 'error';
      
      dispatch({
        type: 'SET_SIMULATION_RESULTS',
        payload: {
          status,
          message: response.final_status_message,
          details: response.raw_simulation_output,
          suggestions: [],
          raw_simulation_output: response.raw_simulation_output,
          warnings_present: response.warnings_present
        }
      });

      if (response.success) {
        enqueueSnackbar(
          response.warnings_present 
            ? 'Simulation completed with warnings' 
            : 'Simulation completed successfully!', 
          { variant: response.warnings_present ? 'warning' : 'success' }
        );
      } else {
        enqueueSnackbar('Simulation failed', { variant: 'error' });
      }
    } catch (error: any) {
      console.error('Simulation error:', error);
      enqueueSnackbar(`Simulation failed: ${error.message}`, { variant: 'error' });
      setSimulationData({
        success: false,
        error_message: error.message,
        final_status_message: 'Simulation failed',
        raw_simulation_output: `Error: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  // Auto-run simulation when page loads
  useEffect(() => {
    if (state.pythonCode && !simulationData && !loading) {
      runSimulation();
    }
  }, []);

  const getStatusIcon = () => {
    if (loading) return <CircularProgress size={24} />;
    if (!simulationData) return null;
    
    if (simulationData.success) {
      return simulationData.warnings_present 
        ? <AlertTriangle size={24} color="orange" />
        : <CheckCircle size={24} color="green" />;
    } else {
      return <XCircle size={24} color="red" />;
    }
  };

  const getStatusColor = (): 'success' | 'warning' | 'error' | 'info' => {
    if (loading) return 'info';
    if (!simulationData) return 'info';
    
    if (simulationData.success) {
      return simulationData.warnings_present ? 'warning' : 'success';
    } else {
      return 'error';
    }
  };

  const getStatusMessage = () => {
    if (loading) return 'Running simulation...';
    if (!simulationData) return 'Preparing simulation...';
    
    return simulationData.final_status_message || 'Simulation complete';
  };

  const getSuggestions = () => {
    const suggestions = [];
    
    if (simulationData?.success) {
      if (simulationData.warnings_present) {
        suggestions.push('Review warnings and consider optimizing your protocol');
        suggestions.push('Check labware compatibility and pipette volumes');
      } else {
        suggestions.push('Protocol is ready to run on your Opentrons robot');
        suggestions.push('Consider running a test with water first');
      }
    } else {
      suggestions.push('Fix the errors identified in the simulation');
      suggestions.push('Review your hardware configuration');
      suggestions.push('Check that all labware and pipettes are properly configured');
    }
    
    return suggestions;
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
            Back to Code Generation
          </Button>
          
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Simulation Results
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            Test your protocol with the Opentrons simulator
          </Typography>
        </Box>

        {/* Simulation Status */}
        <Paper elevation={2} sx={{ p: 4, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            {getStatusIcon()}
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              {getStatusMessage()}
            </Typography>
            {simulationData && (
              <Chip 
                label={simulationData.success ? "PASSED" : "FAILED"} 
                color={getStatusColor()}
                variant="filled"
              />
            )}
          </Box>

          <Alert severity={getStatusColor()} sx={{ mb: 3 }}>
            {loading && "Please wait while we simulate your protocol..."}
            {!loading && simulationData?.success && !simulationData.warnings_present && "Your protocol simulation completed successfully! The code is ready to run."}
            {!loading && simulationData?.success && simulationData.warnings_present && "Simulation completed with warnings. Please review the details below."}
            {!loading && simulationData && !simulationData.success && "Simulation failed. Please review the errors and fix your protocol."}
            {!loading && !simulationData && "Starting simulation..."}
          </Alert>

          {/* Error Message */}
          {simulationData?.error_message && (
            <Alert severity="error" sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Error Details:
              </Typography>
              <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {simulationData.error_message}
              </Typography>
            </Alert>
          )}

          {/* Warning Details */}
          {simulationData?.warnings_present && simulationData?.warning_details && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Warning Details:
              </Typography>
              <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {simulationData.warning_details}
              </Typography>
            </Alert>
          )}

          {/* Suggestions */}
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            Suggestions
          </Typography>
          <List>
            {getSuggestions().map((suggestion, index) => (
              <ListItem key={index}>
                <ListItemText primary={suggestion} />
              </ListItem>
            ))}
          </List>
        </Paper>

        {/* Detailed Simulation Log */}
        {simulationData?.raw_simulation_output && (
          <Paper elevation={2} sx={{ mb: 3 }}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="h6">
                  Detailed Simulation Log
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    bgcolor: 'grey.50', 
                    maxHeight: 400, 
                    overflow: 'auto' 
                  }}
                >
                  <Typography 
                    variant="body2" 
                    component="pre" 
                    sx={{ 
                      fontFamily: 'monospace', 
                      whiteSpace: 'pre-wrap',
                      margin: 0
                    }}
                  >
                    {simulationData.raw_simulation_output}
                  </Typography>
                </Paper>
              </AccordionDetails>
            </Accordion>
          </Paper>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowLeft size={20} />}
            onClick={handleBackToCodeEdit}
          >
            Back to Code Editor
          </Button>
          
          <Button
            variant="contained"
            endIcon={<ChevronRight size={20} />}
            onClick={handleViewAnimation}
            disabled={!simulationData?.success}
          >
            View Animation
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default SimulationResultsPage;