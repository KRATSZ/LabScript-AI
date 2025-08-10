import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Grid, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  useTheme,
  alpha,
  Stack,
  Divider,
  TextField,
  Alert
} from '@mui/material';
import { Upload, FileCode, ArrowRight, Beaker, Zap } from 'lucide-react';
import { useSnackbar } from 'notistack';
import { useAppContext } from '../context/AppContext';
import { codeEditingExamples, getExamplesByCategory, type CodeEditingExample } from '../utils/codeEditingExamples';

const CodeInputPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  
  const [code, setCode] = useState('');
  const [isInfoAlertVisible, setIsInfoAlertVisible] = useState(true);
  const [selectedExample, setSelectedExample] = useState<CodeEditingExample | null>(null);
  const [suggestedInstruction, setSuggestedInstruction] = useState('');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.py')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setCode(content);
        enqueueSnackbar('Python file loaded successfully!', { variant: 'success' });
      };
      reader.readAsText(file);
    } else {
      enqueueSnackbar('Please select a valid Python (.py) file', { variant: 'error' });
    }
    // Reset the input value to allow re-uploading the same file
    event.target.value = '';
  };

  const handleCodeChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCode(event.target.value);
  };

  const handleExampleSelect = (example: CodeEditingExample) => {
    setSelectedExample(example);
    setCode(example.initialCode);
    setSuggestedInstruction(example.suggestedInstruction);
    enqueueSnackbar(`Loaded example: ${example.label}`, { variant: 'success' });
  };

  const handleContinue = () => {
    if (!code.trim()) {
      enqueueSnackbar('Please upload or paste your Python code first', { variant: 'warning' });
      return;
    }

    // Store the code in global state
    dispatch({ type: 'SET_PYTHON_CODE', payload: code });
    
    // If there's a suggested instruction, navigate with it
    if (suggestedInstruction) {
      navigate('/code-editing', { 
        state: { 
          suggestedInstruction,
          exampleInfo: selectedExample ? {
            label: selectedExample.label,
            description: selectedExample.description
          } : null
        }
      });
    } else {
      // Navigate to the AI editing interface
      navigate('/code-editing');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.03)} 0%, ${alpha(theme.palette.secondary.light, 0.03)} 100%)`,
        py: 3
      }}
    >
      <Container maxWidth="lg">
        {/* Header Section - More Compact */}
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1.5 }}>
            <FileCode size={28} color={theme.palette.primary.main} />
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700, 
                ml: 1.5,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Code Input
            </Typography>
          </Box>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              maxWidth: 700, 
              mx: 'auto',
              lineHeight: 1.5,
              fontWeight: 400,
              mb: 1.5
            }}
          >
            Upload or paste your existing Opentrons protocol code to begin AI-powered editing
          </Typography>
          
          {isInfoAlertVisible && (
            <Alert 
              severity="info" 
              onClose={() => setIsInfoAlertVisible(false)}
              sx={{ 
                maxWidth: 500, 
                mx: 'auto',
                borderRadius: 2,
                '& .MuiAlert-message': {
                  textAlign: 'center',
                  fontSize: '0.875rem'
                }
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                🤖 AI-Powered Code Enhancement
              </Typography>
              Upload your protocol and let our AI assistant help you modify, optimize, and validate it through natural conversation.
            </Alert>
          )}
        </Box>

        {/* Main Input Card - Improved Proportions */}
        <Grid container justifyContent="center">
          <Grid item xs={12} md={10} lg={9}>
            <Card 
              elevation={0}
              sx={{
                borderRadius: 2.5,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.12)}`,
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack spacing={3}>
                  {/* File Upload Section */}
                  <Box>
                    <Typography variant="subtitle1" sx={{ mb: 1.5, fontWeight: 600 }}>
                      Upload Python File
                    </Typography>
                    <input
                      accept=".py"
                      style={{ display: 'none' }}
                      id="file-upload"
                      type="file"
                      onChange={handleFileUpload}
                    />
                    <label htmlFor="file-upload">
                      <Button
                        variant="outlined"
                        component="span"
                        fullWidth
                        startIcon={<Upload />}
                        sx={{
                          py: 1.5,
                          borderRadius: 2,
                          borderStyle: 'dashed',
                          borderWidth: 2,
                          borderColor: alpha(theme.palette.primary.main, 0.3),
                          color: theme.palette.primary.main,
                          fontSize: '1rem',
                          '&:hover': {
                            borderColor: theme.palette.primary.main,
                            background: alpha(theme.palette.primary.main, 0.05),
                          }
                        }}
                      >
                        Choose Python (.py) File
                      </Button>
                    </label>
                  </Box>

                  {/* OR Divider */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Divider sx={{ flex: 1 }} />
                    <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 500 }}>
                      OR
                    </Typography>
                    <Divider sx={{ flex: 1 }} />
                  </Box>

                  {/* Example Selection Section - More Compact */}
                  <Box>
                    <Typography variant="subtitle1" sx={{ mb: 1.5, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Beaker size={18} />
                      Try an Example Protocol
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Choose from practical examples to explore AI-powered code editing features
                    </Typography>
                    
                    <Grid container spacing={1.5}>
                      {['migration', 'basic', 'optimization', 'troubleshooting'].map((category) => (
                        <Grid item xs={12} sm={6} md={3} key={category}>
                          <Box>
                            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, textTransform: 'capitalize', fontSize: '0.875rem' }}>
                              {category === 'migration' ? 'Platform Migration' : 
                               category === 'basic' ? 'Basic Protocols' :
                               category === 'optimization' ? 'Optimization' : 'Troubleshooting'}
                            </Typography>
                            <Stack spacing={0.5}>
                              {getExamplesByCategory(category as CodeEditingExample['category']).map((example) => (
                                <Button
                                  key={example.id}
                                  variant={selectedExample?.id === example.id ? "contained" : "outlined"}
                                  size="small"
                                  onClick={() => handleExampleSelect(example)}
                                  sx={{
                                    textAlign: 'left',
                                    justifyContent: 'flex-start',
                                    textTransform: 'none',
                                    borderRadius: 1.5,
                                    py: 0.8,
                                    px: 1.2,
                                    fontSize: '0.8rem'
                                  }}
                                >
                                  {example.label}
                                </Button>
                              ))}
                            </Stack>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                    
                    {selectedExample && (
                      <Alert 
                        severity="info" 
                        sx={{ mt: 2, borderRadius: 2 }}
                        icon={<Zap size={18} />}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                          {selectedExample.label}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {selectedExample.description}
                        </Typography>
                        <Typography variant="caption" sx={{ mt: 1, display: 'block', fontStyle: 'italic' }}>
                          💡 Suggested instruction: "{selectedExample.suggestedInstruction}"
                        </Typography>
                      </Alert>
                    )}
                  </Box>

                  {/* OR Divider */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Divider sx={{ flex: 1 }} />
                    <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 500 }}>
                      OR
                    </Typography>
                    <Divider sx={{ flex: 1 }} />
                  </Box>

                  {/* Code Paste Area - Optimized */}
                  <Box>
                    <Typography variant="subtitle1" sx={{ mb: 1.5, fontWeight: 600 }}>
                      Paste Your Code
                    </Typography>
                    <TextField
                      multiline
                      rows={10}
                      fullWidth
                      variant="outlined"
                      placeholder="# Paste your Opentrons protocol code here
from opentrons import protocol_api

metadata = {
    'protocolName': 'My Protocol',
    'author': 'Your Name',
    'description': 'Protocol description',
    'apiLevel': '2.20'
}

def run(protocol: protocol_api.ProtocolContext):
    # Your protocol steps here
    pass"
                      value={code}
                      onChange={handleCodeChange}
                      sx={{
                        '& .MuiInputBase-root': {
                          fontFamily: "'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace",
                          fontSize: '0.875rem',
                          borderRadius: 2,
                          lineHeight: 1.6,
                        }
                      }}
                    />
                  </Box>

                  {/* Continue Button - Enhanced */}
                  <Box sx={{ textAlign: 'center', pt: 1 }}>
                    <Button
                      variant="contained"
                      size="large"
                      endIcon={<ArrowRight />}
                      onClick={handleContinue}
                      disabled={!code.trim()}
                      sx={{ 
                        py: 1.5, 
                        px: 4,
                        borderRadius: 2,
                        fontWeight: 600,
                        fontSize: '1rem',
                        background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                        boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.25)}`,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          transform: 'translateY(-1px)',
                          boxShadow: `0 6px 24px ${alpha(theme.palette.primary.main, 0.35)}`,
                        },
                        '&:disabled': {
                          background: theme.palette.action.disabledBackground,
                          transform: 'none',
                          boxShadow: 'none',
                        }
                      }}
                    >
                      Continue to AI Editor
                    </Button>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default CodeInputPage; 