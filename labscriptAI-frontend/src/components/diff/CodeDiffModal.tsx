<<<<<<< HEAD
import React from 'react';
import { Diff, Hunk, parseDiff } from 'react-diff-view';
import { Modal, Box, Typography, Button, Stack, useTheme, alpha } from '@mui/material';
import { Check, X } from 'lucide-react';
import 'react-diff-view/style/index.css';

// 创建diff格式的字符串
const createDiffString = (oldCode: string, newCode: string): string => {
  const lines1 = oldCode.split('\n');
  const lines2 = newCode.split('\n');
  
  let diffString = '--- Original\n+++ Modified\n';
  let lineNum1 = 1;
  let lineNum2 = 1;
  
  const maxLines = Math.max(lines1.length, lines2.length);
  let hunkStart1 = 1;
  let hunkStart2 = 1;
  let hunkLines: string[] = [];
  
  for (let i = 0; i < maxLines; i++) {
    const line1 = lines1[i] || '';
    const line2 = lines2[i] || '';
    
    if (line1 === line2) {
      hunkLines.push(` ${line1}`);
    } else {
      if (lines1[i] !== undefined) {
        hunkLines.push(`-${line1}`);
      }
      if (lines2[i] !== undefined) {
        hunkLines.push(`+${line2}`);
      }
    }
  }
  
  if (hunkLines.length > 0) {
    diffString += `@@ -${hunkStart1},${lines1.length} +${hunkStart2},${lines2.length} @@\n`;
    diffString += hunkLines.join('\n');
  }
  
  return diffString;
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
        
        <Box sx={{ flexGrow: 1, overflowY: 'auto', border: `1px solid ${theme.palette.divider}`, borderRadius: 2, p: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Code Changes:</Typography>
          {(() => {
            try {
              const diffString = createDiffString(oldCode, newCode);
              const files = parseDiff(diffString);
              
              return files.map((file, index) => (
                <Diff key={index} viewType="split" diffType={file.type} hunks={file.hunks}>
                  {(hunks) => hunks.map((hunk) => (
                    <Hunk key={hunk.content} hunk={hunk} />
                  ))}
                </Diff>
              ));
            } catch (error) {
              // 如果diff解析失败，显示简单的对比
              return (
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" color="error">Original:</Typography>
                    <Box component="pre" sx={{ 
                      fontSize: '12px', 
                      fontFamily: 'monospace', 
                      backgroundColor: alpha(theme.palette.error.light, 0.1),
                      p: 1,
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: '300px'
                    }}>
                      {oldCode}
                    </Box>
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" color="success.main">Modified:</Typography>
                    <Box component="pre" sx={{ 
                      fontSize: '12px', 
                      fontFamily: 'monospace', 
                      backgroundColor: alpha(theme.palette.success.light, 0.1),
                      p: 1,
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: '300px'
                    }}>
                      {newCode}
                    </Box>
                  </Box>
                </Box>
              );
            }
          })()}
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
=======
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
>>>>>>> upstream/main
