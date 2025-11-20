import React, { useState } from 'react';
import { Box, Typography, Grid, Paper, Tooltip, IconButton, useTheme, alpha, Chip } from '@mui/material';
import { X, Grid3X3, MousePointer } from 'lucide-react';
import { useAppContext } from '../../context/AppContext';

const DeckLayout: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const theme = useTheme();
  const [dragOverSlot, setDragOverSlot] = useState<string | null>(null);
  
  // Generate slots based on robot model (both models now use 4x3 grid)
  const slots = state.robotModel === 'Flex' 
    ? ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3']
    : ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
  
  const handleDrop = (e: React.DragEvent<HTMLDivElement>, slot: string) => {
    e.preventDefault();
    setDragOverSlot(null);
    const labwareData = e.dataTransfer.getData('application/json');
    if (labwareData) {
      const labware = JSON.parse(labwareData);
      dispatch({
        type: 'SET_DECK_LABWARE',
        payload: { slot, labware }
      });
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>, slot: string) => {
    e.preventDefault();
    setDragOverSlot(slot);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    // Only clear dragOverSlot when mouse truly leaves the slot area
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOverSlot(null);
    }
  };
  
  const handleRemoveLabware = (slot: string, e: React.MouseEvent) => {
    e.stopPropagation();
    dispatch({
      type: 'SET_DECK_LABWARE',
      payload: { slot, labware: null }
    });
  };

  // Calculate occupied slots count
  const occupiedSlots = Object.values(state.deckLayout).filter(labware => labware !== null).length;

  return (
    <Box sx={{ mt: 2 }}>
      {/* Statistics Info */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 3,
        p: 2,
        borderRadius: 2,
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Grid3X3 size={24} color={theme.palette.primary.main} />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
              {state.robotModel} Deck Configuration
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Drag labware from left to deck positions
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip 
            label={`${occupiedSlots}/${slots.length} Configured`}
            color={occupiedSlots > 0 ? "primary" : "default"}
            variant="outlined"
            size="small"
            sx={{ fontWeight: 500 }}
          />
        </Box>
      </Box>

      <Grid 
        container 
        spacing={2.5} // Increased spacing
        sx={{ 
          width: '100%',
          maxWidth: '900px', // Increased max width
          mx: 'auto',
        }}
      >
        {slots.map((slot) => {
          const labware = state.deckLayout[slot];
          const isDragOver = dragOverSlot === slot;
          
          return (
            <Grid 
              item 
              xs={12/3} 
              key={slot}
              sx={{
                aspectRatio: '1/1',
              }}
            >
              <Paper
                elevation={0}
                onDrop={(e) => handleDrop(e, slot)}
                onDragOver={handleDragOver}
                onDragEnter={(e) => handleDragEnter(e, slot)}
                onDragLeave={handleDragLeave}
                sx={{
                  height: '160px', // Increased from 140px to 160px
                  minHeight: '160px',
                  border: '3px dashed', // Keep border width
                  borderColor: isDragOver 
                    ? theme.palette.success.main
                    : labware 
                    ? theme.palette.primary.main 
                    : alpha(theme.palette.grey[400], 0.5),
                  borderRadius: 3,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  padding: 2.5, // Increased padding
                  position: 'relative',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  backgroundColor: isDragOver
                    ? alpha(theme.palette.success.main, 0.1)
                    : labware 
                    ? alpha(theme.palette.primary.main, 0.08)
                    : alpha(theme.palette.background.paper, 0.8),
                  backdropFilter: 'blur(10px)',
                  cursor: 'pointer',
                  '&:hover': {
                    borderColor: isDragOver
                      ? theme.palette.success.main
                      : labware 
                      ? theme.palette.primary.main 
                      : theme.palette.primary.light,
                    backgroundColor: isDragOver
                      ? alpha(theme.palette.success.main, 0.15)
                      : labware 
                      ? alpha(theme.palette.primary.main, 0.12)
                      : alpha(theme.palette.primary.main, 0.05),
                    transform: 'translateY(-4px) scale(1.02)',
                    boxShadow: isDragOver
                      ? `0 8px 32px ${alpha(theme.palette.success.main, 0.3)}`
                      : `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                  },
                  // Add drag active state animation
                  ...(isDragOver && {
                    animation: 'dragOverPulse 1s ease-in-out infinite',
                    '@keyframes dragOverPulse': {
                      '0%': {
                        boxShadow: `0 0 0 0 ${alpha(theme.palette.success.main, 0.4)}`,
                      },
                      '70%': {
                        boxShadow: `0 0 0 10px ${alpha(theme.palette.success.main, 0)}`,
                      },
                      '100%': {
                        boxShadow: `0 0 0 0 ${alpha(theme.palette.success.main, 0)}`,
                      },
                    },
                  }),
                }}
              >
                {/* Slot Label */}
                <Typography 
                  variant="body2" 
                  component="div"
                  sx={{ 
                    position: 'absolute',
                    top: 10, // Adjusted for larger size
                    left: 14,
                    fontWeight: 700,
                    fontSize: '1rem', // Increased font size
                    color: isDragOver
                      ? theme.palette.success.main
                      : labware 
                      ? theme.palette.primary.main 
                      : theme.palette.text.secondary,
                    background: alpha(theme.palette.background.paper, 0.9),
                    px: 1.5,
                    py: 0.5,
                    borderRadius: 1,
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  }}
                >
                  {slot}
                </Typography>
                
                {labware ? (
                  <>
                    <Box sx={{ mt: 4.5, textAlign: 'center', px: 1, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                      <Typography 
                        variant="body2" 
                        component="div" 
                        sx={{ 
                          fontWeight: 600,
                          fontSize: '0.9rem', // Slightly increased
                          lineHeight: 1.3,
                          color: theme.palette.primary.main,
                          wordBreak: 'break-word',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          mb: 1.5, // Increased spacing
                        }}
                      >
                        {labware.displayName}
                      </Typography>
                      <Chip
                        label={labware.type}
                        size="small"
                        sx={{
                          fontSize: '0.75rem', // Slightly increased
                          height: 26, // Increased height
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          color: theme.palette.primary.main,
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                          fontWeight: 500,
                        }}
                      />
                    </Box>
                    
                    <Tooltip title="Remove Labware" arrow>
                      <IconButton
                        size="medium"
                        color="primary"
                        onClick={(e) => handleRemoveLabware(slot, e)}
                        sx={{
                          position: 'absolute',
                          top: 10, // Adjusted for larger size
                          right: 10,
                          background: alpha(theme.palette.error.main, 0.1),
                          border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                          color: theme.palette.error.main,
                          backdropFilter: 'blur(10px)',
                          '&:hover': {
                            background: alpha(theme.palette.error.main, 0.2),
                            transform: 'scale(1.1)',
                          }
                        }}
                      >
                        <X size={16} />
                      </IconButton>
                    </Tooltip>
                  </>
                ) : (
                  <Box sx={{ 
                    textAlign: 'center', 
                    color: theme.palette.text.secondary,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 1.5, // Increased gap
                    opacity: isDragOver ? 0.8 : 0.6,
                  }}>
                    <Box
                      sx={{
                        width: 56, // Increased size
                        height: 56,
                        borderRadius: '50%',
                        border: `2px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mb: 1,
                        transition: 'all 0.3s ease',
                        ...(isDragOver && {
                          borderColor: theme.palette.success.main,
                          background: alpha(theme.palette.success.main, 0.1),
                        })
                      }}
                    >
                      <MousePointer size={24} color={isDragOver ? theme.palette.success.main : theme.palette.primary.main} />
                    </Box>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        fontSize: '0.8rem', // Increased font size
                        textAlign: 'center',
                        px: 1,
                        fontWeight: 500,
                        color: isDragOver ? theme.palette.success.main : 'inherit',
                      }}
                    >
                      {isDragOver ? 'Drop labware here' : 'Drag labware here'}
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default DeckLayout;