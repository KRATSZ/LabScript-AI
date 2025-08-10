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
  TextField, 
  CircularProgress,
  Divider, 
  Paper, 
  Chip,
  IconButton,
  useTheme,
  alpha,
  Stack
} from '@mui/material';
import { ArrowRight, Copy, RefreshCw, Save, FileText, Sparkles, Target } from 'lucide-react';
import { useSnackbar } from 'notistack';
import { useAppContext } from '../context/AppContext';
import MarkdownEditor from '../components/sop/MarkdownEditor';
import ChatInterface, { ChatMessage } from '../components/ChatInterface';
import { apiService, formatHardwareConfig } from '../services/api';
import { goalSuggestions } from '../utils/goalSuggestions';

const SopDefinitionPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationComplete, setGenerationComplete] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  
  // Handle user goal input change
  const handleUserGoalChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    dispatch({ type: 'SET_USER_GOAL', payload: event.target.value });
  };
  
  // Handle SOP content change from the markdown editor
  const handleSopChange = (content: string) => {
    dispatch({ type: 'SET_GENERATED_SOP', payload: content });
  };
  
  // Handle SOP generation with streaming API
  const handleGenerateSop = async () => {
    if (!state.userGoal.trim()) {
      enqueueSnackbar('Please enter an experiment description first', { variant: 'warning' });
      return;
    }

    setIsGenerating(true);
    setGenerationComplete(false);
    
    // Clear existing SOP content to show streaming effect
    dispatch({ type: 'SET_GENERATED_SOP', payload: '' });

    try {
      const hardwareConfigForApi = state.rawHardwareConfigText && state.rawHardwareConfigText.trim() !== ''
                                   ? state.rawHardwareConfigText
                                   : formatHardwareConfig(state);

      // Use a ref to track the current SOP content for accurate streaming
      let currentSopContent = '';

      // Use streaming API for real-time generation
      await apiService.generateSOPStream(
        {
          hardware_config: hardwareConfigForApi,
          user_goal: state.userGoal
        },
        // onToken callback - append each token to display
        (token: string) => {
          currentSopContent += token;
          dispatch({ type: 'SET_GENERATED_SOP', payload: currentSopContent });
        },
        // onComplete callback
        () => {
          setGenerationComplete(true);
          setIsGenerating(false);
          enqueueSnackbar('SOP generated successfully!', { variant: 'success' });
        },
        // onError callback
        (error: string) => {
          console.error('SOP generation error:', error);
          enqueueSnackbar(`SOP generation failed: ${error}`, { variant: 'error' });
          
          const fallbackSop = generateSampleSop(state.userGoal);
          dispatch({ type: 'SET_GENERATED_SOP', payload: fallbackSop });
          enqueueSnackbar('Using sample SOP as a fallback', { variant: 'info' });
          
          setIsGenerating(false);
        }
      );
    } catch (error: any) {
      console.error('SOP generation error:', error);
      enqueueSnackbar(`SOP generation failed: ${error.message}`, { variant: 'error' });
      
      const fallbackSop = generateSampleSop(state.userGoal);
      dispatch({ type: 'SET_GENERATED_SOP', payload: fallbackSop });
      enqueueSnackbar('Using sample SOP as a fallback', { variant: 'info' });
      
      setIsGenerating(false);
    }
  };

  const handleEditSop = async (instruction: string) => {
    if (!state.generatedSop.trim()) {
      enqueueSnackbar('Please generate an SOP before editing.', { variant: 'warning' });
      return;
    }

    setIsEditing(true);
    const userMessage: ChatMessage = { sender: 'user', text: instruction };
    setChatMessages(prev => [...prev, userMessage]);

    // Add a placeholder for AI response
    const aiPlaceholderMessage: ChatMessage = { sender: 'ai', text: 'Thinking...' };
    setChatMessages(prev => [...prev, aiPlaceholderMessage]);

    try {
      const hardwareConfigForApi = state.rawHardwareConfigText?.trim() || formatHardwareConfig(state);
      
      const response = await apiService.converseSOP({
        original_sop: state.generatedSop,
        user_instruction: instruction,
        hardware_context: hardwareConfigForApi,
      });

      let aiResponseMessage: ChatMessage;

      if (response.type === 'edit' && response.content) {
        // Update the SOP in the context
        dispatch({ type: 'SET_GENERATED_SOP', payload: response.content });
        aiResponseMessage = { sender: 'ai', text: 'I have updated the SOP based on your instructions. Please review the changes.' };
        enqueueSnackbar('SOP edited successfully!', { variant: 'success' });
      } else if (response.type === 'chat' && response.content) {
        // Just show the chat response, don't change the SOP
        aiResponseMessage = { sender: 'ai', text: response.content };
      } else {
        // Fallback for unexpected response structure
        const fallbackMessage = (response as any).content || "I'm not sure how to handle that. Could you please rephrase?";
        aiResponseMessage = { sender: 'ai', text: fallbackMessage };
        enqueueSnackbar('Received an unexpected response from the server.', { variant: 'warning' });
      }

      // Update the AI message in chat
      setChatMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = aiResponseMessage;
        return newMessages;
      });

    } catch (error: any) {
      console.error('SOP conversation error:', error);
      const errorMessage = `An error occurred: ${error.message}`;
      enqueueSnackbar(errorMessage, { variant: 'error' });
      
      const aiErrorMessage: ChatMessage = { sender: 'ai', text: `Sorry, I couldn't process that. Reason: ${error.message}` };
      setChatMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = aiErrorMessage;
        return newMessages;
      });
    } finally {
      setIsEditing(false);
    }
  };

  const handleClearSopMessages = () => {
    setChatMessages([]);
    enqueueSnackbar('Conversation history cleared', { variant: 'info' });
  };
  
  // Generate code and navigate to code generation page
  const handleGenerateCode = () => {
    navigate('/generate-code');
  };
  
  // Sample SOP generation based on user goal (fallback)
  const generateSampleSop = (userGoal: string) => {
    return `# Protocol: ${userGoal.split('.')[0]}

## Materials Required

- ${state.robotModel} robot
- ${state.leftPipette ? `Left pipette: ${state.leftPipette}` : ''}
- ${state.rightPipette ? `Right pipette: ${state.rightPipette}` : ''}
${Object.entries(state.deckLayout)
  .filter(([_, labware]) => labware !== null)
  .map(([slot, labware]) => `- ${labware?.displayName} at position ${slot}`)
  .join('\n')}

## Procedure

1. **Initialization**
   - Initialize robot and check all components
   - Ensure all labware is properly placed

2. **Sample Preparation**
   - Load samples into appropriate wells
   - Prepare any necessary reagents

3. **Protocol Steps**
   - Transfer solutions between containers
   - Mix as needed
   - Incubate if required by the protocol

4. **Completion**
   - Properly store all samples
   - Clean workspace and pipettes

## Notes
- Ensure all tips are available before starting
- Verify liquid levels in all containers
- Follow proper laboratory safety procedures
`;
  };
  
  useEffect(() => {
    document.title = 'Define SOP - LabScript AI';
  }, []);
  
  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
        py: 4
      }}
    >
      <Container maxWidth="lg">
        {/* Header Section */}
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <FileText size={32} color={theme.palette.primary.main} />
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
              Define Your Protocol Procedure
            </Typography>
          </Box>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              maxWidth: 600, 
              mx: 'auto',
              lineHeight: 1.6,
              fontWeight: 400
            }}
          >
            Transform your experimental ideas into detailed Standard Operating Procedures with AI assistance
          </Typography>
        </Box>
        
        <Grid container spacing={4}>
          <Grid item xs={12} md={8}>
            <Stack spacing={4}>
              {/* User Goal Input */}
              <Card 
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  }
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                      }}
                    >
                      <Target size={24} color={theme.palette.primary.main} />
                    </Box>
                    <Box>
                      <Typography variant="h5" component="h2" sx={{ fontWeight: 700, mb: 0.5 }}>
                        Experiment Description
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Tell us about your experiment in detail - the more specific, the better the AI-generated SOP
                      </Typography>
                    </Box>
                  </Stack>
                  
                  <TextField
                    fullWidth
                    multiline
                    rows={8}
                    variant="outlined"
                    placeholder="Example: I want to perform a PCR cleanup protocol using magnetic beads for 96 samples in a 96-well plate. The protocol should include bead binding, washing steps with 70% ethanol, and elution of cleaned PCR products into a new plate. Each sample volume is 50μL and I want to elute in 30μL of elution buffer."
                    value={state.userGoal}
                    onChange={handleUserGoalChange}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        fontSize: '1rem',
                        lineHeight: 1.6,
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: alpha(theme.palette.primary.main, 0.3),
                          }
                        },
                        '&.Mui-focused': {
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: theme.palette.primary.main,
                            borderWidth: 2,
                          }
                        }
                      },
                      '& .MuiInputBase-input': {
                        padding: '16px',
                      }
                    }}
                  />
                  
                  {/* Quick Goal Suggestions */}
                  <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mr: 1, alignSelf: 'center' }}>
                      Quick examples:
                    </Typography>
                    {goalSuggestions.map((suggestion) => (
                      <Button
                        key={suggestion.title}
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          dispatch({ type: 'SET_USER_GOAL', payload: suggestion.text });
                          enqueueSnackbar(`Example loaded: ${suggestion.title}`, { variant: 'info' });
                        }}
                        sx={{
                          borderRadius: 2,
                          fontWeight: 500,
                          textTransform: 'none',
                          borderColor: alpha(theme.palette.primary.main, 0.3),
                          color: theme.palette.primary.main,
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            borderColor: theme.palette.primary.main,
                            background: alpha(theme.palette.primary.main, 0.05),
                            transform: 'translateY(-1px)',
                          }
                        }}
                      >
                        {suggestion.title}
                      </Button>
                    ))}
                  </Box>
                  
                  <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      size="large"
                      onClick={handleGenerateSop}
                      disabled={!state.userGoal.trim() || isGenerating || isEditing}
                      startIcon={(isGenerating || isEditing) ? <CircularProgress size={20} color="inherit" /> : <Sparkles />}
                      sx={{
                        py: 1.5,
                        px: 4,
                        borderRadius: 2,
                        fontWeight: 600,
                        fontSize: '1rem',
                        background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                        boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.4)}`,
                        },
                        '&:disabled': {
                          background: theme.palette.action.disabledBackground,
                          transform: 'none',
                          boxShadow: 'none',
                        }
                      }}
                    >
                      {isGenerating ? 'Generating...' : isEditing ? 'Editing...' : 'Generate SOP with AI'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
              
              {/* Generated SOP */}
              <Card 
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                  backdropFilter: 'blur(10px)',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  }
                }}
              >
                <CardContent sx={{ p: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Stack direction="row" alignItems="center" spacing={2}>
                      <Box
                        sx={{
                          p: 1.5,
                          borderRadius: 2,
                          background: `linear-gradient(45deg, ${alpha(theme.palette.success.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                        }}
                      >
                        <FileText size={24} color={theme.palette.success.main} />
                      </Box>
                      <Typography variant="h5" component="h2" sx={{ fontWeight: 700 }}>
                        Standard Operating Procedure (SOP)
                      </Typography>
                    </Stack>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip 
                        label={state.generatedSop ? "AI Generated" : "Ready to Generate"}
                        size="medium"
                        color={state.generatedSop ? "success" : "default"}
                        variant={state.generatedSop ? "filled" : "outlined"}
                        sx={{ 
                          fontWeight: 600,
                          ...(state.generatedSop && {
                            background: `linear-gradient(45deg, ${alpha(theme.palette.success.main, 0.8)}, ${alpha(theme.palette.success.dark, 0.9)})`,
                            color: 'white'
                          })
                        }}
                      />
                      
                      {state.generatedSop && (
                        <IconButton 
                          size="medium" 
                          color="primary"
                          onClick={() => {
                            navigator.clipboard.writeText(state.generatedSop);
                            enqueueSnackbar('SOP copied to clipboard', { variant: 'success' });
                          }}
                          title="Copy to clipboard"
                          sx={{
                            borderRadius: 2,
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              background: alpha(theme.palette.primary.main, 0.1),
                              transform: 'scale(1.1)',
                            }
                          }}
                        >
                          <Copy size={20} />
                        </IconButton>
                      )}
                    </Box>
                  </Box>
                  
                  <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 3 }}>
                    Review and edit the AI-generated SOP below. Make any necessary adjustments before proceeding to code generation.
                  </Typography>

                  {(isGenerating || isEditing) && !state.generatedSop && (
                    <Box 
                      sx={{ 
                        textAlign: 'center', 
                        my: 6,
                        p: 4,
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
                      }}
                    >
                      <CircularProgress 
                        size={80} 
                        thickness={3} 
                        color="primary"
                        sx={{
                          filter: `drop-shadow(0 4px 8px ${alpha(theme.palette.primary.main, 0.3)})`
                        }}
                      />
                      <Typography variant="h5" sx={{ mt: 3, fontWeight: 600 }}>
                        {isEditing ? 'Applying Your Edits...' : 'Generating Your SOP...'}
                      </Typography>
                      <Typography variant="body1" color="text.secondary" sx={{ mt: 1, maxWidth: 400, mx: 'auto' }}>
                        {isEditing 
                          ? 'Our AI is rewriting the SOP based on your instructions.'
                          : 'Our AI is analyzing your requirements and creating a detailed Standard Operating Procedure tailored to your experiment.'
                        }
                      </Typography>
                    </Box>
                  )}
                  
                  <MarkdownEditor 
                    value={state.generatedSop} 
                    onChange={handleSopChange}
                    placeholder="Your detailed SOP will appear here after generation. You can also write your own SOP manually if preferred."
                  />
                  
                  {generationComplete && (
                    <Paper 
                      elevation={0} 
                      sx={{ 
                        mt: 3, 
                        p: 3, 
                        borderRadius: 2,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.success.light, 0.1)} 0%, ${alpha(theme.palette.success.main, 0.05)} 100%)`,
                        border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
                      }}
                    >
                      <Stack direction="row" alignItems="center" spacing={2}>
                        <Box
                          sx={{
                            p: 1,
                            borderRadius: 1,
                            background: alpha(theme.palette.success.main, 0.1),
                          }}
                        >
                          <Sparkles size={20} color={theme.palette.success.main} />
                        </Box>
                        <Typography variant="body1" color="success.dark" sx={{ fontWeight: 600 }}>
                          SOP generated successfully! You can now review and edit the SOP above before proceeding to code generation.
                        </Typography>
                      </Stack>
                    </Paper>
                  )}
                </CardContent>
              </Card>
            </Stack>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ height: 'calc(100vh - 200px)', position: 'sticky', top: '100px' }}>
              <ChatInterface 
                messages={chatMessages}
                onSubmit={handleEditSop}
                isProcessing={isEditing}
                title="Conversational SOP Edit"
                placeholder="e.g., Use 80% ethanol instead of 70%."
                onClearMessages={handleClearSopMessages}
              />
            </Box>
          </Grid>

          {/* Navigation Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button
                variant="outlined"
                size="large"
                onClick={() => navigate('/configure-hardware')}
                sx={{
                  py: 1.5,
                  px: 4,
                  borderRadius: 2,
                  fontWeight: 600,
                  borderColor: alpha(theme.palette.primary.main, 0.3),
                  color: theme.palette.primary.main,
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    borderColor: theme.palette.primary.main,
                    background: alpha(theme.palette.primary.main, 0.05),
                    transform: 'translateY(-2px)',
                  }
                }}
              >
                Back to Hardware Configuration
              </Button>
              
              <Button
                variant="contained"
                color="primary"
                size="large"
                endIcon={<ArrowRight />}
                onClick={handleGenerateCode}
                disabled={!state.generatedSop.trim() || isGenerating || isEditing}
                sx={{ 
                  py: 1.5, 
                  px: 4,
                  borderRadius: 2,
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  boxShadow: `0 6px 24px ${alpha(theme.palette.primary.main, 0.3)}`,
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-3px)',
                    boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.4)}`,
                  },
                  '&:disabled': {
                    background: theme.palette.action.disabledBackground,
                    transform: 'none',
                    boxShadow: 'none',
                  }
                }}
              >
                Generate Protocol Code
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default SopDefinitionPage;