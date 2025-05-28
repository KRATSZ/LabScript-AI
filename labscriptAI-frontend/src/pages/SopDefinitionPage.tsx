import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  TextField,
  Container,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import { ChevronRight, ArrowLeft, Wand2, FileText } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { apiService, formatHardwareConfig } from '../services/api';
import { useSnackbar } from 'notistack';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SopDefinitionPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);
  const [sopGenerated, setSopGenerated] = useState(false);

  const handleBack = () => {
    navigate('/configure-hardware');
  };

  const handleNext = () => {
    if (!state.generatedSop.trim()) {
      enqueueSnackbar('Please generate or enter an SOP before proceeding', { variant: 'warning' });
      return;
    }
    navigate('/generate-code');
  };

  const handleGenerateSOP = async () => {
    if (!state.userGoal.trim()) {
      enqueueSnackbar('Please enter your experiment description first', { variant: 'warning' });
      return;
    }

    setLoading(true);
    try {
      const hardwareConfig = state.rawHardwareConfigText || formatHardwareConfig(state);
      
      const response = await apiService.generateSOP({
        hardware_config: hardwareConfig,
        user_goal: state.userGoal
      });

      if (response.success) {
        dispatch({ type: 'SET_GENERATED_SOP', payload: response.sop_markdown });
        setSopGenerated(true);
        enqueueSnackbar('SOP generated successfully!', { variant: 'success' });
      } else {
        throw new Error('SOP generation failed');
      }
    } catch (error: any) {
      console.error('SOP generation error:', error);
      enqueueSnackbar(`Failed to generate SOP: ${error.message}`, { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleUserGoalChange = (goal: string) => {
    dispatch({ type: 'SET_USER_GOAL', payload: goal });
  };

  const handleSopChange = (sop: string) => {
    dispatch({ type: 'SET_GENERATED_SOP', payload: sop });
  };

  useEffect(() => {
    setSopGenerated(!!state.generatedSop.trim());
  }, [state.generatedSop]);

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
            Back to Hardware Config
          </Button>
          
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Define Standard Operating Procedure
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            Describe your experiment and generate a detailed SOP with AI assistance
          </Typography>
        </Box>

        {/* Experiment Description */}
        <Paper elevation={2} sx={{ p: 4, mb: 3 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
            Experiment Description
          </Typography>
          
          <TextField
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            label="Describe your experiment goal"
            placeholder="e.g., Perform a serial dilution from column 1 to column 12 of a 96-well plate using a 1:2 dilution ratio..."
            value={state.userGoal}
            onChange={(e) => handleUserGoalChange(e.target.value)}
            sx={{ mb: 3 }}
          />
          
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Wand2 size={20} />}
            onClick={handleGenerateSOP}
            disabled={loading || !state.userGoal.trim()}
            size="large"
          >
            {loading ? 'Generating SOP...' : 'Generate SOP with AI'}
          </Button>
        </Paper>

        {/* Generated SOP */}
        <Paper elevation={2} sx={{ p: 4, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FileText size={24} style={{ marginRight: 8 }} />
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Standard Operating Procedure
            </Typography>
            <Chip 
              label={sopGenerated ? "Generated" : "Not Generated"} 
              color={sopGenerated ? "success" : "default"} 
              size="small" 
              sx={{ ml: 2 }} 
            />
          </Box>
          
          {sopGenerated ? (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                Review and edit the generated SOP as needed. You can modify the content directly in the editor below.
              </Alert>
              
              <TextField
                fullWidth
                multiline
                rows={12}
                variant="outlined"
                label="Generated SOP (Markdown)"
                value={state.generatedSop}
                onChange={(e) => handleSopChange(e.target.value)}
                sx={{ mb: 3, fontFamily: 'monospace' }}
              />
              
              {/* Markdown Preview */}
              <Typography variant="h6" gutterBottom>
                Preview:
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {state.generatedSop}
                </ReactMarkdown>
              </Paper>
            </Box>
          ) : (
            <Alert severity="info">
              Click "Generate SOP with AI" above to create a detailed standard operating procedure based on your experiment description.
            </Alert>
          )}
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
          <Button
            variant="contained"
            endIcon={<ChevronRight size={20} />}
            onClick={handleNext}
            size="large"
            disabled={!state.generatedSop.trim()}
          >
            Generate Protocol Code
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default SopDefinitionPage;