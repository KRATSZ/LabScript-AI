import React from 'react';
import { Box } from '@mui/material';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface CodeViewerProps {
  code: string;
  language: string;
}

const CodeViewer: React.FC<CodeViewerProps> = ({ code, language }) => {
  return (
    <Box sx={{ fontSize: '14px' }}>
      <SyntaxHighlighter
        language={language}
        style={atomOneDark}
        showLineNumbers
        customStyle={{
          margin: 0,
          padding: '16px',
          borderRadius: '4px',
          fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
          minHeight: '100%',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </Box>
  );
};

export default CodeViewer;