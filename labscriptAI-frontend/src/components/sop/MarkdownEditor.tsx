import React from 'react';
import { Box, TextField } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './MarkdownStyles.css';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({ value, onChange, placeholder }) => {
  const [isEditing, setIsEditing] = React.useState(false);
  
  const handleBlur = () => {
    setIsEditing(false);
  };
  
  const handleChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(event.target.value);
  };
  
  return (
    <Box>
      {isEditing ? (
        <TextField
          autoFocus
          fullWidth
          multiline
          rows={15}
          variant="outlined"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder={placeholder}
          sx={{
            fontFamily: 'monospace',
            '& .MuiOutlinedInput-root': {
              fontFamily: 'monospace',
            }
          }}
        />
      ) : (
        <Box
          onClick={() => setIsEditing(true)}
          sx={{
            cursor: 'pointer',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'grey.300',
            p: 2,
            minHeight: '300px',
            maxHeight: '500px',
            overflow: 'auto',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'grey.50',
            },
          }}
        >
          {value ? (
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {value}
              </ReactMarkdown>
            </div>
          ) : (
            <Box sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
              {placeholder}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default MarkdownEditor;