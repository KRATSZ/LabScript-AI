import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  Stack,
  IconButton,
  CircularProgress,
  useTheme,
  alpha,
  Tooltip,
  Divider,
  Fade
} from '@mui/material';
import { Send, Bot, User, Trash2, MessageCircle, Sparkles } from 'lucide-react';

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  isIntermediate?: boolean;
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSubmit: (message: string) => Promise<void>;
  isProcessing: boolean;
  title?: string;
  placeholder?: string;
  onClearMessages?: () => void;
  initialMessage?: string;
  showTitle?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  messages, 
  onSubmit, 
  isProcessing,
  title = "Conversational Edit",
  placeholder = "e.g., Change the pipette to p1000...",
  onClearMessages,
  initialMessage = "",
  showTitle = true
}) => {
  const theme = useTheme();
  const [inputValue, setInputValue] = useState('');
  const [isInputFocused, setIsInputFocused] = useState(false);
  const chatHistoryRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    if (initialMessage) {
      setInputValue(initialMessage);
    }
  }, [initialMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isProcessing) {
      await onSubmit(inputValue);
      setInputValue('');
    }
  };

  const handleClearMessages = () => {
    if (onClearMessages) {
      onClearMessages();
    }
  };

  return (
    <Paper 
      elevation={0}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: 2,
        border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
        background: 'transparent',
        boxShadow: 'none',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header with title and clear button */}
      {showTitle && (
        <Box sx={{ 
          p: 2, 
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          borderTopLeftRadius: 2,
          borderTopRightRadius: 2,
        }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={1.5}>
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1.5,
                  background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                }}
              >
                <MessageCircle size={20} color={theme.palette.primary.main} />
              </Box>
              <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.text.primary }}>
                {title}
              </Typography>
            </Stack>
            
            {onClearMessages && messages.length > 0 && (
              <Tooltip title="Clear conversation history">
                <IconButton
                  onClick={handleClearMessages}
                  size="small"
                  sx={{
                    background: alpha(theme.palette.error.main, 0.1),
                    color: theme.palette.error.main,
                    border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      background: alpha(theme.palette.error.main, 0.2),
                      transform: 'scale(1.05)',
                    }
                  }}
                >
                  <Trash2 size={16} />
                </IconButton>
              </Tooltip>
            )}
          </Stack>
        </Box>
      )}
      
      {/* Chat History */}
      <Box 
        ref={chatHistoryRef}
        sx={{ 
          flexGrow: 1, 
          overflowY: 'auto',
          p: 1.5,
          // Improved scrollbar style
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: alpha(theme.palette.divider, 0.4),
            borderRadius: '3px',
          },
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ 
            textAlign: 'center', 
            color: theme.palette.text.secondary,
            pt: 6,
            pb: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 2
          }}>
            <Box
              sx={{
                p: 2,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
              }}
            >
              <Sparkles size={32} color={theme.palette.primary.main} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: theme.palette.text.primary }}>
              Ready to help!
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8, maxWidth: 280, mx: 'auto', lineHeight: 1.6 }}>
              Ask me to modify, improve, or explain anything about your protocol. I can help with specific changes or general optimizations.
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" sx={{ 
                px: 2, 
                py: 0.5, 
                borderRadius: 1, 
                background: alpha(theme.palette.info.main, 0.1),
                color: theme.palette.info.main,
                fontWeight: 500
              }}>
                💡 Try: "Use 80% ethanol instead" or "Add a mixing step"
              </Typography>
            </Box>
          </Box>
        ) : (
          <Stack spacing={2.5}>
            {messages.map((msg, index) => (
              <Fade in={true} timeout={300} key={index}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    gap: 1.5,
                  }}
                >
                  <Box
                    sx={{
                      p: 1.2,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: msg.sender === 'user' 
                        ? `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                        : alpha(theme.palette.background.default, 0.8),
                      color: msg.sender === 'user' ? 'white' : theme.palette.text.primary,
                      border: msg.sender === 'user' ? 'none' : `1px solid ${alpha(theme.palette.divider, 0.3)}`,
                      mt: 0.5,
                    }}
                  >
                    {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </Box>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 1.5,
                      borderRadius: 2.5, // Softer corners
                      bgcolor: msg.sender === 'user' 
                        ? theme.palette.primary.main
                        : msg.isIntermediate 
                          ? 'transparent' 
                          : alpha(theme.palette.background.default, 0.9),
                      color: msg.sender === 'user' ? 'white' : theme.palette.text.primary,
                      border: `1px solid ${msg.isIntermediate ? 'transparent' : alpha(theme.palette.divider, 0.1)}`,
                      maxWidth: '85%',
                      fontStyle: msg.isIntermediate ? 'italic' : 'normal',
                      opacity: msg.isIntermediate ? 0.8 : 1,
                      backdropFilter: msg.isIntermediate ? 'none' : 'blur(10px)',
                    }}
                  >
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        whiteSpace: 'pre-wrap', 
                        wordWrap: 'break-word',
                        lineHeight: 1.6,
                      }}
                    >
                      {msg.text}
                    </Typography>
                  </Paper>
                </Box>
              </Fade>
            ))}
            {isProcessing && !messages.some(m => m.isIntermediate) && (
              <Fade in={true} timeout={300}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, pl: 6 }}>
                  <CircularProgress size={16} thickness={5} color="info" />
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    AI is thinking...
                  </Typography>
                </Box>
              </Fade>
            )}
          </Stack>
        )}
      </Box>

      {/* Input Area */}
      <Box sx={{ p: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.2)}` }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
          <TextField
            fullWidth
            variant="outlined"
            size="small"
            placeholder={placeholder}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isProcessing}
            autoComplete="off"
            multiline
            maxRows={2}
            minRows={1}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                fontSize: '0.9rem',
              },
            }}
          />
          <IconButton 
            type="submit" 
            color="primary"
            disabled={isProcessing || !inputValue.trim()}
            sx={{
              borderRadius: 2,
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              color: 'white',
              width: 40,
              height: 40,
              '&:disabled': {
                background: theme.palette.action.disabledBackground,
              }
            }}
          >
            {isProcessing ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <Send size={18}/>
            )}
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatInterface; 