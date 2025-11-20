import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Grid, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Stack,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { Play, Copy, Code2, RotateCcw, MessageSquare, Edit3, ArrowLeft, Trash2, Download, Terminal, ChevronDown } from 'lucide-react';
import { useSnackbar } from 'notistack';
import { useAppContext } from '../context/AppContext';
import Editor from "@monaco-editor/react";
import ChatInterface, { ChatMessage } from '../components/ChatInterface';
import CodeDiffModal from '../components/diff/CodeDiffModal';

// Quick edit templates for common code modifications
const quickEditTemplates = [
  {
    key: 'change_pipette',
    label: 'Change Pipette/Instrument',
    template: 'Change the pipette from [current pipette name] to [new pipette name], and move the mount from [left/right] to [left/right]'
  },
  {
    key: 'modify_deck_layout',
    label: 'Modify Deck Layout',
    template: 'Move the labware "[labware name]" from slot [current slot] to slot [new slot]'
  },
  {
    key: 'adjust_liquid_parameters',
    label: 'Adjust Liquid Transfer Parameters',
    template: 'In step [step number], change the liquid transfer volume from [source location] to [target location] from [current volume] μL to [new volume] μL'
  },
  {
    key: 'add_modify_steps',
    label: 'Add/Modify/Delete Steps',
    template: 'At step [position], [add/modify/delete] the following operation: [detailed description of new experimental step]'
  },
  {
    key: 'optimize_speed',
    label: 'Optimize Experiment Speed',
    template: 'Optimize protocol execution speed, focusing on [specific steps or operations] to improve efficiency'
  },
  {
    key: 'migrate_ot2_to_flex',
    label: 'Migrate OT-2 to Opentrons Flex',
    template: 'Please adapt this OT-2 protocol for the Opentrons Flex. Update the API from metadata to requirements, change deck slots from numeric (like "1", "2") to alphanumeric (like "A1", "B2"), and update labware and instruments to be compatible with the Flex robot.'
  },
  {
    key: 'migrate_flex_to_ot2',
    label: 'Migrate Opentrons Flex to OT-2',
    template: 'Please adapt this Flex protocol for the OT-2. Update the API from requirements to metadata, change deck slots from alphanumeric (like "A1", "B2") to numeric strings (like "1", "2"), and update labware and instruments to be compatible with the OT-2 robot.'
  },
  {
    key: 'custom',
    label: 'Custom Instruction...',
    template: ''
  }
];

interface DebugLog {
  timestamp: string;
  message: string;
}

const DebugLogPanel = ({ logs }: { logs: DebugLog[] }) => {
  const theme = useTheme();
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <Card 
      elevation={0}
      sx={{ 
        mt: 1,
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        borderRadius: 2,
        background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
      }}
    >
      <CardContent sx={{ p: 1.5 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1, fontWeight: 600 }}>
          <Terminal size={16} />
          Agent Activity Log
        </Typography>
        <Paper 
          ref={logContainerRef} 
          elevation={0} 
          sx={{ 
            p: 1.5, 
            height: 150, // Increased height for better readability
            overflowY: 'auto', 
            bgcolor: alpha(theme.palette.background.default, 0.3),
            border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.8rem', // Increased font size
            color: theme.palette.text.secondary,
            '&::-webkit-scrollbar': {
              width: '4px',
            },
            '&::-webkit-scrollbar-track': {
              background: 'transparent',
            },
            '&::-webkit-scrollbar-thumb': {
              background: alpha(theme.palette.divider, 0.4),
              borderRadius: '2px',
            },
          }}
        >
          {logs.length === 0 ? (
            <Typography variant="caption" sx={{ opacity: 0.7, fontStyle: 'italic' }}>
              Waiting for agent activity...
            </Typography>
          ) : (
            logs.map((log, index) => (
              <div key={index} style={{ marginBottom: '4px', lineHeight: '1.4' }}>
                <span style={{ color: theme.palette.info.main }}>{`[${log.timestamp}] `}</span>
                <span>{log.message}</span>
              </div>
            ))
          )}
        </Paper>
      </CardContent>
    </Card>
  );
};

interface LocationState {
  suggestedInstruction?: string;
  exampleInfo?: {
    label: string;
    description: string;
  };
}

const CodeEditingPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  
  const [editedCode, setEditedCode] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [diffData, setDiffData] = useState<{ oldCode: string; newCode: string; } | null>(null);
  const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);
  const isInitialized = useRef(false);

  useEffect(() => {
    document.title = 'AI Code Editor - LabScript AI';
    
    // Check if we have code from the input page
    if (state.pythonCode) {
      setEditedCode(state.pythonCode);
      
      // Check if we have suggested instructions from example selection
      if (location.state && !isInitialized.current) {
        const { suggestedInstruction, exampleInfo } = location.state as LocationState;
        if (suggestedInstruction && exampleInfo) {
          // Add a helpful message about the loaded example
          const welcomeMessage: ChatMessage = {
            sender: 'ai',
            text: `I've loaded the "${exampleInfo.label}" example for you. ${exampleInfo.description}\n\n💡 Try this suggested instruction: "${suggestedInstruction}"\n\nFeel free to modify the suggestion or ask me anything else about this protocol!`
          };
          setChatMessages([welcomeMessage]);
          isInitialized.current = true;
        }
      }
    } else {
      // If no code is available, redirect to input page
      navigate('/code-input');
    }
  }, [state.pythonCode, navigate, location.state]);

  const handleTemplateChange = (event: SelectChangeEvent<string>) => {
    const templateKey = event.target.value;
    setSelectedTemplate(templateKey);
  };

  const handleEditCode = async (instruction: string) => {
    if (!editedCode.trim()) {
      enqueueSnackbar('No code available to edit', { variant: 'warning' });
      return;
    }

    setIsEditing(true);
    setDebugLogs([]); // Clear previous logs
    const userMessage: ChatMessage = { sender: 'user', text: instruction };
    setChatMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/converse-code-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({
          original_code: editedCode,
          user_instruction: instruction,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server responded with ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep the last partial message in the buffer

        for (const line of lines) {
          if (line.startsWith('data:')) {
            const jsonStr = line.substring(5).trim();
            if (jsonStr) {
              try {
                const data = JSON.parse(jsonStr);

                // Centralized log handling for any event with a message
                if (data.message) {
                  setDebugLogs(prev => [...prev, { timestamp: new Date().toLocaleTimeString(), message: data.message }]);
                }

                if (data.event_type === 'intermediate_step') {
                  // This is a thinking step from the agent
                  const thinkingMessage: ChatMessage = {
                    sender: 'ai',
                    text: data.message || 'Thinking...',
                    isIntermediate: true,
                  };
                  // Replace the last intermediate message or add a new one
                  setChatMessages(prev => {
                    const lastMessage = prev[prev.length - 1];
                    if (lastMessage && lastMessage.isIntermediate) {
                      return [...prev.slice(0, -1), thinkingMessage];
                    }
                    return [...prev, thinkingMessage];
                  });

                } else if (data.event_type === 'final_result') {
                   // Clear any intermediate "thinking" messages
                   setChatMessages(prev => prev.filter(m => !m.isIntermediate));

                  if (data.type === 'edit') {
                    // Show diff modal instead of applying directly
                    setDiffData({ oldCode: editedCode, newCode: data.content });
                    setChatMessages(prev => [...prev, { sender: 'ai', text: 'I have prepared the code modifications. Please review and apply the changes.' }]);
                  } else {
                    // Robustly handle chat responses to prevent rendering errors
                    const aiResponse = typeof data.content === 'string' 
                      ? data.content 
                      : `[AGENT DEV INFO] Received non-string response: ${JSON.stringify(data.content, null, 2)}`;
                    setChatMessages(prev => [...prev, { sender: 'ai', text: aiResponse }]);
                  }
                } else if (data.event_type === 'error') {
                   // Clear any intermediate "thinking" messages
                   setChatMessages(prev => prev.filter(m => !m.isIntermediate));
                  setChatMessages(prev => [...prev, { sender: 'ai', text: `An error occurred: ${data.message}` }]);
                  enqueueSnackbar(`Stream error: ${data.message}`, { variant: 'error' });
                }
              } catch (e) {
                // Ignore parsing errors for incomplete JSON
                if (!(e instanceof SyntaxError)) {
                    console.error('Error processing stream data:', e);
                }
              }
            }
          }
        }
      }
    } catch (err) {
      console.error("Fetch stream failed:", err);
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      enqueueSnackbar(`Failed to connect to the server for live updates. ${errorMessage}`, { variant: 'error' });
    } finally {
      setIsEditing(false);
    }
  };

  const handleClearMessages = () => {
    setChatMessages([]);
    enqueueSnackbar('Conversation history cleared', { variant: 'info' });
  };

  const handleCopyCode = () => {
    if (editedCode) {
      navigator.clipboard.writeText(editedCode);
      enqueueSnackbar('Code copied to clipboard', { variant: 'success' });
    }
  };

  const handleResetCode = () => {
    if (state.pythonCode) {
      setEditedCode(state.pythonCode);
      enqueueSnackbar('Code reset to original', { variant: 'info' });
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    setEditedCode(value || '');
  };

  const handleApplyDiff = () => {
    if (diffData) {
      setEditedCode(diffData.newCode);
      dispatch({ type: 'SET_PYTHON_CODE', payload: diffData.newCode });
      setDiffData(null);
      enqueueSnackbar('Changes applied to the editor!', { variant: 'success' });
    }
  };

  const handleDiscardDiff = () => {
    setDiffData(null);
    enqueueSnackbar('Changes discarded.', { variant: 'info' });
  };

  const handleRunSimulation = () => {
    if (!editedCode.trim()) {
      enqueueSnackbar('No code available to simulate', { variant: 'warning' });
      return;
    }
    
    dispatch({ type: 'SET_PYTHON_CODE', payload: editedCode });
    navigate('/simulation-results');
  };

  const handleBackToInput = () => {
    navigate('/code-input');
  };

  const handleExportCode = () => {
    const blob = new Blob([editedCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'protocol.py';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    enqueueSnackbar('Code exported successfully!', { variant: 'success' });
  };

  const getTemplatePrompt = () => {
    const template = quickEditTemplates.find(t => t.key === selectedTemplate);
    return template?.template || '';
  };

  return (
    <Box
      sx={{
        height: '100vh',
        width: '100%',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.03)} 0%, ${alpha(theme.palette.secondary.light, 0.03)} 100%)`,
        p: 1,
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header Section - More Compact */}
      <Box sx={{ mb: 1, textAlign: 'center', flexShrink: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Edit3 size={24} color={theme.palette.primary.main} />
          <Typography 
            variant="h5" 
            component="h1" 
            sx={{ 
              fontWeight: 700, 
              ml: 1,
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AI Code Editor
          </Typography>
        </Box>
      </Box>

      {/* Diff Modal */}
      {diffData && (
        <CodeDiffModal
          isOpen={!!diffData}
          oldCode={diffData.oldCode}
          newCode={diffData.newCode}
          onApply={handleApplyDiff}
          onDiscard={handleDiscardDiff}
        />
      )}

      {/* Main Content - Enhanced Layout */}
      <Grid container spacing={1.5} sx={{ flexGrow: 1, overflow: 'hidden', minHeight: 0 }}>
        {/* Left Column: Chat Interface */}
        <Grid item xs={12} md={5} sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Chat Interface Card */}
          <Card 
            elevation={0}
            sx={{
              borderRadius: 2,
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              border: `1px solid ${alpha(theme.palette.secondary.main, 0.1)}`,
              background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
              backdropFilter: 'blur(10px)',
              minHeight: 0,
            }}
          >
            <CardContent sx={{ p: 1.5, flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1} sx={{ mb: 1.5 }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Box
                    sx={{
                      p: 0.8,
                      borderRadius: 1.5,
                      background: `linear-gradient(45deg, ${alpha(theme.palette.secondary.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                    }}
                  >
                    <MessageSquare size={18} color={theme.palette.secondary.main} />
                  </Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    AI Assistant
                  </Typography>
                </Stack>
                <Tooltip title="Clear conversation">
                  <IconButton onClick={handleClearMessages} size="small" color="default">
                    <Trash2 size={16} />
                  </IconButton>
                </Tooltip>
              </Stack>

              {/* Quick Templates */}
              <Box sx={{ mb: 1.5, flexShrink: 0 }}>
                <FormControl fullWidth variant="outlined" size="small">
                  <InputLabel id="template-select-label">Quick Edit Templates</InputLabel>
                  <Select
                    labelId="template-select-label"
                    value={selectedTemplate}
                    label="Quick Edit Templates"
                    onChange={handleTemplateChange}
                    sx={{ borderRadius: 1.5, fontSize: '0.875rem' }}
                  >
                    {quickEditTemplates.map((template) => (
                      <MenuItem key={template.key} value={template.key}>
                        {template.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              {/* Chat Interface */}
              <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <ChatInterface
                  messages={chatMessages}
                  onSubmit={handleEditCode}
                  onClearMessages={handleClearMessages}
                  isProcessing={isEditing}
                  title=""
                  placeholder={selectedTemplate ? getTemplatePrompt() : "e.g., Change the pipette to p1000..."}
                  initialMessage={selectedTemplate ? getTemplatePrompt() : ""}
                  showTitle={false}
                />
              </Box>
            </CardContent>
          </Card>

          {/* Debug Log Panel is now outside this grid */}
        </Grid>

        {/* Right Column: Code Editor */}
        <Grid item xs={12} md={7} sx={{ display: 'flex', flexDirection: 'column' }}>
          <Card 
            elevation={0}
            sx={{
              borderRadius: 2,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
              background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
              backdropFilter: 'blur(10px)',
            }}
          >
            <CardContent sx={{ p: 1.5, flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Box
                    sx={{
                      p: 0.8,
                      borderRadius: 1.5,
                      background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                    }}
                  >
                    <Code2 size={18} color={theme.palette.primary.main} />
                  </Box>
                  <Typography variant="subtitle1" component="h2" sx={{ fontWeight: 600 }}>
                    Protocol Code
                  </Typography>
                </Stack>
                
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <Tooltip title="Reset to original code">
                    <Box component="span" sx={{ display: 'inline-flex' }}>
                      <IconButton onClick={handleResetCode} color="warning" disabled={!state.pythonCode || isEditing} size="small">
                        <RotateCcw size={16} />
                      </IconButton>
                    </Box>
                  </Tooltip>
                  <Tooltip title="Copy code">
                    <Box component="span" sx={{ display: 'inline-flex' }}>
                      <IconButton onClick={handleCopyCode} color="primary" disabled={!editedCode} size="small">
                        <Copy size={16} />
                      </IconButton>
                    </Box>
                  </Tooltip>
                  <Tooltip title="Export to .py file">
                    <Box component="span" sx={{ display: 'inline-flex' }}>
                      <IconButton onClick={handleExportCode} color="success" disabled={!editedCode} size="small">
                        <Download size={16} />
                      </IconButton>
                    </Box>
                  </Tooltip>
                  <Divider orientation="vertical" flexItem sx={{ mx: 0.5, height: 24 }} />
                  <Tooltip title="Back to Input">
                    <IconButton onClick={handleBackToInput} color="default" size="small">
                      <ArrowLeft size={16} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Run Simulation">
                      <Box component="span" sx={{ display: 'inline-flex', ml: 0.5 }}>
                          <Button
                          variant="contained"
                          color="primary"
                          size="small"
                          startIcon={<Play size={14} />}
                          onClick={handleRunSimulation}
                          disabled={!editedCode.trim() || isEditing}
                          sx={{ borderRadius: 1.5, fontWeight: 600, fontSize: '0.8rem', px: 1.5 }}
                          >
                          Simulate
                          </Button>
                      </Box>
                  </Tooltip>
                </Stack>
              </Box>
              
              <Paper
                elevation={0}
                sx={{ 
                  flexGrow: 1,
                  position: 'relative',
                  border: `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                  borderRadius: 1.5, 
                  overflow: 'hidden',
                }}
              >
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  value={editedCode}
                  onChange={handleEditorChange}
                  options={{
                    theme: 'vs-light',
                    fontSize: 14, // Increased font size
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    readOnly: isEditing,
                    lineNumbers: 'on',
                    folding: true,
                    wordWrap: 'on',
                    fontFamily: "Arial, 'Helvetica Neue', Helvetica, sans-serif", // Set to Arial as requested
                    lineHeight: 1.6,
                    padding: { top: 16, bottom: 16 },
                  }}
                />
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Agent Activity Log at the bottom, collapsible */}
      {isEditing && (
        <Box sx={{ flexShrink: 0, pt: 1, backdropFilter: 'blur(10px)' }}>
          <Accordion 
            elevation={0} 
            sx={{ 
              borderRadius: 2,
              border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
              background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
              '&:before': { display: 'none' },
            }}
          >
            <AccordionSummary
              expandIcon={<ChevronDown size={20} />}
              sx={{ '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 1 } }}
            >
              <Terminal size={16} />
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>Agent Activity Log</Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0, pb: 1, px: 1 }}>
              <DebugLogPanel logs={debugLogs} />
            </AccordionDetails>
          </Accordion>
        </Box>
      )}
    </Box>
  );
};

export default CodeEditingPage;