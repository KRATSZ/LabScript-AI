import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import { Box, Typography } from '@mui/material';
import { I18nextProvider } from 'react-i18next';

import '../../../web/opentrons-protocol-visualizer-web-slim/components/src/styles/global.css';
import '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/global.css';

import { i18n as visualizerI18n } from '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/i18n';
import { VisualizerContainer } from '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/viz/VisualizerContainer';

import type { ProtocolAnalysisOutput } from '../../../web/opentrons-protocol-visualizer-web-slim/shared-data/js';

interface ErrorBoundaryProps {
  children: ReactNode;
  resetKey: string;
}

interface ErrorBoundaryState {
  error: Error | null;
}

class VisualizerErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(
      'Integrated protocol visualizer render error:',
      error,
      info.componentStack
    );
  }

  override componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  override render(): ReactNode {
    if (this.state.error != null) {
      return (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            p: 3,
            backgroundColor: '#fff',
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Animation view render failed
          </Typography>
          <Typography variant="body2" color="text.secondary">
            The analysis finished, but the playback renderer could not process
            this protocol. Try re-running the analysis after simplifying the
            protocol.
          </Typography>
          <Box
            component="pre"
            sx={{
              m: 0,
              p: 2,
              borderRadius: 1,
              bgcolor: 'rgba(211, 47, 47, 0.08)',
              color: '#d32f2f',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
            }}
          >
            {this.state.error.message}
          </Box>
        </Box>
      );
    }

    return this.props.children;
  }
}

interface IntegratedProtocolVisualizerProps {
  analysisOutput: ProtocolAnalysisOutput;
}

const IntegratedProtocolVisualizer: React.FC<
  IntegratedProtocolVisualizerProps
> = ({ analysisOutput }) => {
  return (
    <I18nextProvider i18n={visualizerI18n}>
      <VisualizerErrorBoundary resetKey={analysisOutput.createdAt}>
        <VisualizerContainer analysisOutput={analysisOutput} />
      </VisualizerErrorBoundary>
    </I18nextProvider>
  );
};

export default IntegratedProtocolVisualizer;
