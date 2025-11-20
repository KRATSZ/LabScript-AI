import React from 'react';
import ReactDiffViewer from 'react-diff-viewer';
import { Modal, Box, Typography, Button, Stack, useTheme, alpha, IconButton } from '@mui/material';
import { Check, X } from 'lucide-react';

// Since @types/react-diff-viewer is not available, we can define a basic type for styles
// This is optional but helps with type safety.
type DiffViewerStyles = {
  [key: string]: React.CSSProperties;
};

interface CodeDiffModalProps {
  isOpen: boolean;
  oldCode: string;
  newCode: string;
  onApply: () => void;
  onDiscard: () => void;
}

const modalStyle = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '90%',
  maxWidth: '1400px',
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  display: 'flex',
  flexDirection: 'column',
  maxHeight: '90vh',
  borderRadius: 2,
};

const CodeDiffModal: React.FC<CodeDiffModalProps> = ({ isOpen, oldCode, newCode, onApply, onDiscard }) => {
  const theme = useTheme();

  // Custom styles for the diff viewer to match the app's theme
  const diffStyles: DiffViewerStyles = {
    variables: {
      light: {
        diffViewerBackground: '#fdfdfd',
        addedBackground: alpha(theme.palette.success.light, 0.3),
        removedBackground: alpha(theme.palette.error.light, 0.3),
        wordAddedBackground: alpha(theme.palette.success.main, 0.4),
        wordRemovedBackground: alpha(theme.palette.error.main, 0.4),
        addedGutterBackground: alpha(theme.palette.success.light, 0.2),
        removedGutterBackground: alpha(theme.palette.error.light, 0.2),
        gutterBackground: '#f7f7f7',
        gutterBackgroundDark: '#f3f1f1',
      },
    },
    diffContainer: {
      borderRadius: '8px',
      border: `1px solid ${theme.palette.divider}`,
    },
    line: {
      fontFamily: 'monospace',
      fontSize: '14px',
    },
  };

  return (
    <Modal
      open={isOpen}
      onClose={onDiscard}
      aria-labelledby="code-diff-modal-title"
      aria-describedby="code-diff-modal-description"
    >
      <Box sx={modalStyle}>
        <Typography id="code-diff-modal-title" variant="h6" component="h2" sx={{ mb: 2, fontWeight: 700 }}>
          Confirm Code Changes
        </Typography>
        
        <Box sx={{ flexGrow: 1, overflowY: 'auto', border: `1px solid ${theme.palette.divider}`, borderRadius: 2 }}>
          <ReactDiffViewer
            oldValue={oldCode}
            newValue={newCode}
            splitView={true}
            useDarkTheme={theme.palette.mode === 'dark'}
            leftTitle="Original Code"
            rightTitle="AI Modified Code (Verified)"
            styles={diffStyles}
            showDiffOnly={false} // Show full file for context
          />
        </Box>

        <Stack direction="row" justifyContent="flex-end" spacing={2} sx={{ mt: 3 }}>
          <Button 
            variant="outlined" 
            color="secondary" 
            onClick={onDiscard} 
            startIcon={<X size={18} />}
            sx={{ borderRadius: 2, fontWeight: 600 }}
          >
            Discard
          </Button>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={onApply} 
            startIcon={<Check size={18} />}
            sx={{ borderRadius: 2, fontWeight: 600 }}
          >
            Apply Changes
          </Button>
        </Stack>
      </Box>
    </Modal>
  );
};

export default CodeDiffModal; 