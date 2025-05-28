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
  ListItemText,
  Divider
} from '@mui/material';
import { ChevronRight, ArrowLeft, Play, ExpandMore, Code, AlertTriangle } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { apiService, formatHardwareConfig } from '../services/api';
import { useSnackbar } from 'notistack';
import Editor from '@monaco-editor/react';

const CodeGenerationPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState('');
  const [generationComplete, setGenerationComplete] = useState(false);
  const [iterationLogs, setIterationLogs] = useState<Array<Record<string, any>>>([]);
  const [attempts, setAttempts] = useState(0);
  const [warnings, setWarnings] = useState<string[]>([]);

  const handleBack = () => {
    navigate('/define-sop');
  };

  const handleRunSimulation = () => {
    if (!state.pythonCode.trim()) {
      enqueueSnackbar('No code available to simulate', { variant: 'warning' });
      return;
    }
    navigate('/simulation-results');
  };

  const handleGenerateCode = async () => {
    if (!state.generatedSop.trim()) {
      enqueueSnackbar('Please generate an SOP first', { variant: 'warning' });
      return;
    }

    setLoading(true);
    setProgress('Starting code generation...');
    setIterationLogs([]);
    setAttempts(0);
    setWarnings([]);
    setGenerationComplete(false);

    try {
      const hardwareConfig = state.rawHardwareConfigText || formatHardwareConfig(state);
      
      const response = await apiService.generateProtocolCode(
        {
          sop_markdown: state.generatedSop,
          hardware_config: hardwareConfig
        },
        (progressMessage) => {
          setProgress(progressMessage);
        }
      );

      if (response.success) {
        dispatch({ type: 'SET_PYTHON_CODE', payload: response.generated_code });
        setAttempts(response.attempts);
        setWarnings(response.warnings || []);
        setIterationLogs(response.iteration_logs || []);
        setGenerationComplete(true);
        enqueueSnackbar('Code generation successful!', { variant: 'success' });
      } else {
        throw new Error('Code generation failed');
      }
    } catch (error: any) {
      console.error('Code generation error:', error);
      enqueueSnackbar(`Code generation failed: ${error.message}`, { variant: 'error' });
      setProgress(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (value: string | undefined) => {
    if (value !== undefined) {
      dispatch({ type: 'SET_PYTHON_CODE', payload: value });
    }
  };

  // Auto-generate code when page loads if we have an SOP
  useEffect(() => {
    if (state.generatedSop && !state.pythonCode && !loading) {
      handleGenerateCode();
    }
  }, []);

  const renderIterationLog = (log: Record<string, any>, index: number) => {
    const eventType = log.event_type || 'unknown';
    const attemptNum = log.attempt_num || 0;
    const message = log.message || '';
    
    let icon = null;
    let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
    
    switch (eventType) {
      case 'iteration_log':
        icon = <Code size={16} />;
        color = 'primary';
        break;
      case 'llm_call_start':
        icon = <CircularProgress size={16} />;
        color = 'info';
        break;
      case 'code_attempt':
        icon = <Code size={16} />;
        color = 'secondary';
        break;
      case 'simulation_start':
        icon = <Play size={16} />;
        color = 'info';
        break;
      case 'simulation_result':
        const status = log.status || '';
        if (status.includes('SUCCEEDED')) {
          color = 'success';
        } else if (status.includes('FAILED')) {
          color = 'error';
          icon = <AlertTriangle size={16} />;
        }
        break;
      case 'iteration_result':
        const iterStatus = log.status || '';
        if (iterStatus === 'SUCCESS') {
          color = 'success';
        } else if (iterStatus.includes('FAILED')) {
          color = 'error';
          icon = <AlertTriangle size={16} />;
        } else if (iterStatus.includes('WARNING')) {
          color = 'warning';
          icon = <AlertTriangle size={16} />;
        }
        break;
    }

    return (
      <ListItem key={index} divider>
        <ListItemText
          primary={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {icon}
              <Chip 
                label={`Attempt ${attemptNum}`} 
                size="small" 
                color={color}
              />
              <Typography variant="body2" component="span">
                {eventType.replace('_', ' ').toUpperCase()}
              </Typography>
            </Box>
          }
          secondary={
            <Box sx={{ mt: 1 }}>
              {message && (
                <Typography variant="body2" color="text.secondary">
                  {message}
                </Typography>
              )}
              {log.generated_code && (
                <Paper variant="outlined" sx={{ p: 1, mt: 1, bgcolor: 'grey.50' }}>
                  <Typography variant="caption" component="pre" sx={{ fontFamily: 'monospace' }}>
                    {log.generated_code.length > 200 
                      ? log.generated_code.substring(0, 200) + '...' 
                      : log.generated_code}
                  </Typography>
                </Paper>
              )}
              {log.error_details && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  <Typography variant="caption">
                    {log.error_details}
                  </Typography>
                </Alert>
              )}
            </Box>
          }
        />
      </ListItem>
    );
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
            Back to SOP Definition
          </Button>
          
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Generate Protocol Code
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            AI-powered Python code generation for your Opentrons protocol
          </Typography>
        </Box>

        {/* Progress and Status */}
        {(loading || progress) && (
          <Alert 
            severity={loading ? "info" : generationComplete ? "success" : "warning"} 
            sx={{ mb: 3 }}
            icon={loading ? <CircularProgress size={20} /> : undefined}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2">
                {progress}
              </Typography>
              {attempts > 0 && (
                <Chip label={`${attempts} attempts`} size="small" />
              )}
              {warnings.length > 0 && (
                <Chip label={`${warnings.length} warnings`} size="small" color="warning" />
              )}
            </Box>
          </Alert>
        )}

        {/* Generated Code */}
        <Paper elevation={2} sx={{ mb: 3 }}>
          <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Generated Protocol Code
            </Typography>
            {!state.pythonCode && !loading && (
              <Button
                variant="contained"
                startIcon={<Code size={20} />}
                onClick={handleGenerateCode}
                sx={{ mt: 2 }}
              >
                Auto-generate Code
              </Button>
            )}
          </Box>
          
          <Box sx={{ height: 650 }}>
            <Editor
              height="100%"
              defaultLanguage="python"
              value={state.pythonCode}
              onChange={handleCodeChange}
              options={{
                fontSize: 14,
                fontFamily: 'Fira Code, Monaco, monospace',
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
              }}
              theme="vs"
            />
          </Box>
        </Paper>

        {/* Iteration Logs */}
        {iterationLogs.length > 0 && (
          <Paper elevation={2} sx={{ mb: 3 }}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="h6">
                  Detailed Iteration Logs ({iterationLogs.length} events)
                </Typography>
              </AccordionSummary>
              <AccordionDetails sx={{ p: 0 }}>
                <List dense>
                  {iterationLogs.map((log, index) => renderIterationLog(log, index))}
                </List>
              </AccordionDetails>
            </Accordion>
          </Paper>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Code Generation Warnings:
            </Typography>
            <List dense>
              {warnings.map((warning, index) => (
                <ListItem key={index}>
                  <ListItemText primary={warning} />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
          <Button
            variant="contained"
            endIcon={<Play size={20} />}
            onClick={handleRunSimulation}
            size="large"
            disabled={!state.pythonCode.trim()}
          >
            Run Simulation
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default CodeGenerationPage;