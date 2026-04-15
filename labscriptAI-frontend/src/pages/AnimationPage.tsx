import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Typography,
  alpha,
  useTheme,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  FileCode2,
  Monitor,
  RefreshCcw,
} from 'lucide-react';
import { useSnackbar } from 'notistack';

import IntegratedProtocolVisualizer from '../components/IntegratedProtocolVisualizer';
import { useAppContext } from '../context/AppContext';
import {
  analyzeProtocolForVisualization,
  type VisualizerAnalyzeProgressPhase,
} from '../services/api';
import { normalizeAnalysisOutput } from '../../../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/src/normalizeAnalysisOutput';

import type { ProtocolAnalysisOutput } from '../../../web/opentrons-protocol-visualizer-web-slim/shared-data/js';

const PHASE_LABEL: Record<VisualizerAnalyzeProgressPhase, string> = {
  submitting: 'Submitting protocol to analyzer…',
  submitted: 'Protocol submitted, waiting for worker…',
  queued: 'Waiting in analyzer queue…',
  running: 'Building animation timeline…',
};

const safeFilePart = (value: string): string =>
  value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'protocol';

const AnimationPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const analysisRunIdRef = useRef(0);

  const [analysisOutput, setAnalysisOutput] = useState<ProtocolAnalysisOutput | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [progressPhase, setProgressPhase] =
    useState<VisualizerAnalyzeProgressPhase | null>(null);
  const [lastAnalyzedAt, setLastAnalyzedAt] = useState<Date | null>(null);
  const [reanalysisNonce, setReanalysisNonce] = useState(0);

  const isOpentronsProtocol = state.robotModel !== 'PyLabRobot';
  const canAnalyzeProtocol = Boolean(state.pythonCode.trim()) && isOpentronsProtocol;
  const protocolFilename = useMemo(() => {
    const robot = safeFilePart(state.robotModel || 'opentrons');
    const date = new Date().toISOString().slice(0, 10);
    return `labscriptai-${robot}-${date}.py`;
  }, [state.robotModel]);

  const runVisualizerAnalysis = useCallback(async () => {
    if (!canAnalyzeProtocol) {
      setAnalysisOutput(null);
      setAnalysisError(null);
      setAnalysisLoading(false);
      setProgressPhase(null);
      return;
    }

    const runId = analysisRunIdRef.current + 1;
    analysisRunIdRef.current = runId;
    const protocolFile = new File([state.pythonCode], protocolFilename, {
      type: 'text/x-python',
    });

    setAnalysisLoading(true);
    setAnalysisError(null);
    setProgressPhase('submitting');

    try {
      const result = await analyzeProtocolForVisualization(protocolFile, {
        check: state.simulationResults.status === 'success',
        onProgress: phase => {
          if (analysisRunIdRef.current === runId) {
            setProgressPhase(phase);
          }
        },
      });

      if (analysisRunIdRef.current !== runId) {
        return;
      }

      setAnalysisOutput(normalizeAnalysisOutput(result));
      setLastAnalyzedAt(new Date());
    } catch (error) {
      if (analysisRunIdRef.current !== runId) {
        return;
      }

      const message =
        error instanceof Error ? error.message : 'Failed to analyze protocol for playback.';
      setAnalysisError(message);
      setAnalysisOutput(null);
    } finally {
      if (analysisRunIdRef.current === runId) {
        setAnalysisLoading(false);
        setProgressPhase(null);
      }
    }
  }, [
    canAnalyzeProtocol,
    protocolFilename,
    state.pythonCode,
    state.simulationResults.status,
  ]);

  useEffect(() => {
    document.title = 'Protocol Animation - LabScript AI';
  }, []);

  useEffect(() => {
    void runVisualizerAnalysis();
  }, [runVisualizerAnalysis, reanalysisNonce]);

  const handleAnalyzeAgain = (): void => {
    setReanalysisNonce(prev => prev + 1);
    enqueueSnackbar('Re-running protocol analysis for animation preview', {
      variant: 'success',
    });
  };

  const analysisErrorCount = analysisOutput?.errors.length ?? 0;

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        <Box sx={{ mb: 5, textAlign: 'center' }}>
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="center"
            spacing={2}
            sx={{ mb: 2 }}
          >
            <Monitor size={32} color={theme.palette.primary.main} />
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 800,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Protocol Animation
            </Typography>
          </Stack>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 820, mx: 'auto', lineHeight: 1.6, fontWeight: 400 }}
          >
            Review the generated Opentrons deck replay before running the robot.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} lg={3}>
            <Stack spacing={3}>
              <Card
                elevation={0}
                sx={{
                  borderRadius: 1,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.14)}`,
                  background: alpha(theme.palette.background.paper, 0.92),
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 3 }}>
                    <FileCode2 size={22} color={theme.palette.primary.main} />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Animation Input
                    </Typography>
                  </Stack>

                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                        Protocol file
                      </Typography>
                      <Typography
                        variant="body1"
                        sx={{ fontWeight: 600, wordBreak: 'break-word' }}
                      >
                        {protocolFilename}
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                        Robot
                      </Typography>
                      <Chip
                        label={state.robotModel}
                        color="primary"
                        variant="outlined"
                        size="small"
                      />
                    </Box>

                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                        Simulation
                      </Typography>
                      <Chip
                        icon={
                          state.simulationResults.status === 'success' ? (
                            <CheckCircle size={16} />
                          ) : (
                            <AlertTriangle size={16} />
                          )
                        }
                        label={state.simulationResults.status.toUpperCase()}
                        color={
                          state.simulationResults.status === 'success'
                            ? 'success'
                            : 'warning'
                        }
                        variant="outlined"
                        size="small"
                      />
                    </Box>

                    {analysisOutput != null && (
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.75 }}>
                          Analysis
                        </Typography>
                        <Chip
                          label={
                            analysisErrorCount === 0
                              ? 'Ready'
                              : `${analysisErrorCount} analysis error${
                                  analysisErrorCount === 1 ? '' : 's'
                                }`
                          }
                          color={analysisErrorCount === 0 ? 'success' : 'warning'}
                          variant="outlined"
                          size="small"
                        />
                      </Box>
                    )}
                  </Stack>

                  <Stack spacing={1.5} sx={{ mt: 3 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<RefreshCcw />}
                      onClick={handleAnalyzeAgain}
                      disabled={!canAnalyzeProtocol || analysisLoading}
                      sx={{ py: 1.25, borderRadius: 1, fontWeight: 700 }}
                    >
                      Analyze Again
                    </Button>
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={<ArrowLeft />}
                      onClick={() => navigate('/simulation-results')}
                      sx={{ py: 1.25, borderRadius: 1, fontWeight: 700 }}
                    >
                      Back to Simulation
                    </Button>
                  </Stack>
                </CardContent>
              </Card>

              {!state.pythonCode.trim() && (
                <Alert severity="warning" sx={{ borderRadius: 1 }}>
                  Generate protocol code before opening the animation preview.
                </Alert>
              )}

              {!isOpentronsProtocol && (
                <Alert severity="info" sx={{ borderRadius: 1 }}>
                  The integrated visualizer analyzes Opentrons protocols. PyLabRobot
                  protocols still need a compatible external viewer.
                </Alert>
              )}

              {analysisLoading && progressPhase != null && (
                <Alert severity="info" sx={{ borderRadius: 1 }}>
                  {PHASE_LABEL[progressPhase]}
                </Alert>
              )}

              {analysisError != null && (
                <Alert severity="error" sx={{ borderRadius: 1 }}>
                  {analysisError}
                </Alert>
              )}

              {lastAnalyzedAt != null && (
                <Alert severity="success" sx={{ borderRadius: 1 }}>
                  Last analyzed at {lastAnalyzedAt.toLocaleTimeString()}.
                </Alert>
              )}
            </Stack>
          </Grid>

          <Grid item xs={12} lg={9}>
            <Paper
              elevation={0}
              sx={{
                position: 'relative',
                height: { xs: 680, lg: 'calc(100vh - 260px)' },
                minHeight: 680,
                borderRadius: 1,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.18)}`,
                overflow: 'hidden',
                background: theme.palette.background.paper,
              }}
            >
              {analysisLoading && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    zIndex: 1,
                  }}
                >
                  <LinearProgress />
                </Box>
              )}

              {!canAnalyzeProtocol ? (
                <Stack
                  spacing={2}
                  alignItems="center"
                  justifyContent="center"
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    background: alpha(theme.palette.background.paper, 0.86),
                  }}
                >
                  <Monitor size={28} color={theme.palette.primary.main} />
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    Generate Opentrons protocol code to render the animation preview.
                  </Typography>
                </Stack>
              ) : analysisOutput != null ? (
                <IntegratedProtocolVisualizer analysisOutput={analysisOutput} />
              ) : (
                <Stack
                  spacing={2}
                  alignItems="center"
                  justifyContent="center"
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    background: alpha(theme.palette.background.paper, 0.86),
                  }}
                >
                  <RefreshCcw size={28} color={theme.palette.primary.main} />
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {progressPhase != null
                      ? PHASE_LABEL[progressPhase]
                      : analysisError ?? 'Preparing animation preview...'}
                  </Typography>
                </Stack>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default AnimationPage;
