import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Grid, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  LinearProgress,
  useTheme,
  alpha,
  Stack,
  Chip,
  Divider,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { ArrowLeft, Play, RefreshCw, Copy, Code2, Zap, CheckCircle, AlertTriangle, Clock, FileCode, Brain, Cpu, TestTube, Repeat, Info } from 'lucide-react';
import { useSnackbar } from 'notistack';
import { useAppContext } from '../context/AppContext';
import Editor from "@monaco-editor/react";
import { formatHardwareConfig } from '../services/api';
import type { IterationLog } from '../services/api';

interface ApiErrorDetail {
  error: string;
  details: string;
}

interface ApiError {
  response?: {
    data?: {
      detail?: ApiErrorDetail | string;
    };
  };
  message?: string;
}

const CodeGenerationPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState('');
  const [warnings, setWarnings] = useState<string[]>([]);
  const [attempts, setAttempts] = useState(0);
  const [editedCode, setEditedCode] = useState(state.pythonCode);
  const [generationStartTime, setGenerationStartTime] = useState<Date | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(0);
  const [showProcessExplanation, setShowProcessExplanation] = useState(false);
  const [showReadyAlert, setShowReadyAlert] = useState(true);
  const [iterationLogs, setIterationLogs] = useState<IterationLog[]>([]);

  // Generation steps definition
  const generationSteps = [
    { 
      label: 'Parse SOP Requirements', 
      description: 'AI is analyzing your standard operating procedure, understanding experimental steps and hardware requirements',
      icon: <Brain size={20} />,
      estimatedTime: 15
    },
    { 
      label: 'Generate Initial Code', 
      description: 'Generate Opentrons Python protocol code based on SOP, including all necessary hardware configurations',
      icon: <Code2 size={20} />,
      estimatedTime: 30
    },
    { 
      label: 'Simulation Validation', 
      description: 'Run Opentrons simulator to validate code syntax and logical correctness',
      icon: <TestTube size={20} />,
      estimatedTime: 20
    },
    { 
      label: 'Smart Optimization', 
      description: 'If issues are found, AI will automatically analyze errors and generate improved versions (may require multiple iterations)',
      icon: <Repeat size={20} />,
      estimatedTime: 45
    }
  ];

  // Pre-estimate total time (seconds)
  const getTotalEstimatedTime = () => {
    return generationSteps.reduce((total, step) => total + step.estimatedTime, 0);
  };

  // Auto-generate code
  useEffect(() => {
    // Only auto-trigger if SOP exists, there is no current Python code, and not already generating
    if (state.generatedSop && !state.pythonCode && !isGenerating) {
      console.log("[CodeGenerationPage] useEffect triggering handleGenerateCode");
      // Show process explanation, then automatically start
      setShowProcessExplanation(true);
      setTimeout(() => {
        handleGenerateCode();
      }, 2000); // Give user 2 seconds to see explanation
    }
  }, [state.generatedSop, state.pythonCode]);

  // Note: Using real server-sent events instead of fake progress bar

  const handleGenerateCode = async () => {
    if (!state.generatedSop) {
      enqueueSnackbar('Please generate SOP first', { variant: 'warning' });
      navigate('/define-sop');
      return;
    }

    setIsGenerating(true);
    setGenerationStartTime(new Date());
    setProgress('Starting intelligent code generation process...');
    setWarnings([]);
    setAttempts(0);
    setEditedCode(''); // Clear previous code
    setCurrentStep(0);
    setEstimatedTime(0);
    setShowProcessExplanation(true);
    setIterationLogs([]); // Reset logs
    dispatch({ type: 'SET_PYTHON_CODE', payload: '' });

    try {
      const hardwareConfigForApi = state.rawHardwareConfigText?.trim() || formatHardwareConfig(state);
      
      // Create EventSource connection to streaming API
      const eventSource = new EventSource('https://api.ai4ot.cn/api/generate-protocol-code');
      
      // Send request data to server
      // Note: EventSource doesn't directly support POST requests, we need another approach
      // We will pass data through URL parameters or other methods, or use fetch to initialize connection
      
      // Close current connection first, use fetch to initiate POST request and get streaming response
      eventSource.close();
      
      const response = await fetch('https://api.ai4ot.cn/api/generate-protocol-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          sop_markdown: state.generatedSop,
          hardware_config: hardwareConfigForApi,
          robot_model: state.robotModel // Explicitly pass robot model for accurate backend dispatch
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      let buffer = '';
      
      // 读取流式响应
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        
        // 处理 SSE 消息
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保留不完整的行
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)); // 移除 'data: ' 前缀
              
              // 处理不同类型的事件
              switch (data.event_type) {
                case 'start':
                  setProgress(data.message || 'Starting code generation...');
                  setCurrentStep(0);
                  break;
                  
                case 'initialization':
                  setProgress(data.message || 'Initialization complete');
                  setAttempts(0);
                  break;
                  
                case 'node_complete': {
                  // 保留完整的原始事件信息，不再转换为自定义类型
                  const nodeCompleteEntry: IterationLog = {
                    event_type: 'node_complete',
                    node_name: data.node_name,
                    attempt_num: data.attempt_num,
                    message: data.message,
                    timestamp: data.timestamp,
                    // 根据节点类型保留不同的详细信息
                    ...(data.node_name === 'generator' && {
                      has_code: data.has_code
                    }),
                    ...(data.node_name === 'simulator' && {
                      simulation_success: data.simulation_success,
                      has_warnings: data.has_warnings,
                      error_details: data.error_details || ''
                    }),
                    ...(data.node_name === 'feedback_preparer' && {
                      has_feedback: data.has_feedback,
                      error_analysis: data.error_analysis || ''
                    })
                  };
                  setIterationLogs(prev => [...prev, nodeCompleteEntry]);
                  
                  // 更新UI状态
                  if (data.node_name === 'generator') {
                    setProgress(`Code generation attempt ${data.attempt_num} complete`);
                    setAttempts(data.attempt_num || 0);
                    setCurrentStep(1);
                  } else if (data.node_name === 'simulator') {
                    setProgress(`Simulation validation for attempt ${data.attempt_num} complete: ${data.simulation_success ? 'Success' : 'Failure'}`);
                    setCurrentStep(2);
                  } else if (data.node_name === 'feedback_preparer') {
                    setProgress(`Error analysis for attempt ${data.attempt_num} complete, preparing for next iteration`);
                    setCurrentStep(3);
                  }
                  break;
                }
                  
                case 'attempt_result': {
                  const logEntry: IterationLog = {
                    event_type: 'attempt_result',
                    attempt_num: data.attempt_num,
                    status: data.status,
                    message: data.message,
                    final_code: data.final_code || '',
                    error_details: data.error_details || '',
                    warning_details: data.warning_details || '',
                    timestamp: data.timestamp
                  };
                  setIterationLogs(prev => [...prev, logEntry]);
                  
                  setProgress(data.message || `Attempt ${data.attempt_num} completed`);
                  break;
                }
                  
                case 'final_result':
                  setIsGenerating(false);
                  setShowProcessExplanation(false);
                  setCurrentStep(generationSteps.length - 1);
                  
                  if (data.status === 'success') {
                    const finalCode = data.generated_code || '';
                    dispatch({ type: 'SET_PYTHON_CODE', payload: finalCode });
                    setEditedCode(finalCode);
                    setAttempts(data.total_attempts || 0);
                    
                    if (data.has_warnings) {
                      setWarnings([data.warning_details || 'Code generated with warnings']);
                      setProgress(`✅ Code generation successful with warnings! (${data.total_attempts} attempts)`);
                      enqueueSnackbar('Code generated successfully with warnings', { variant: 'warning' });
                    } else {
                      setProgress(`🎉 Code generation perfectly successful! (${data.total_attempts} attempts)`);
                      enqueueSnackbar('Code generation successful!', { variant: 'success' });
                    }
                  } else {
                    // 处理失败情况
                    const finalCode = data.generated_code || '';
                    const errorReport = data.error_report || '';
                    
                    if (finalCode) {
                      dispatch({ type: 'SET_PYTHON_CODE', payload: finalCode });
                      setEditedCode(finalCode);
                    }
                    
                    setAttempts(data.total_attempts || 0);
                    setWarnings([data.error_details || 'Code generation failed']);
                    setProgress(`❌ Code generation failed after ${data.total_attempts} attempts`);
                    enqueueSnackbar('Code generation failed', { variant: 'error' });
                    
                    // 显示错误报告
                    console.error('Code generation error report:', errorReport);
                  }
                  break;
                  
                case 'error':
                  setIsGenerating(false);
                  setShowProcessExplanation(false);
                  setProgress('❌ Error occurred during code generation');
                  enqueueSnackbar(data.message || 'Code generation error', { variant: 'error' });
                  console.error('Code generation error:', data);
                  break;
                  
                case 'stream_complete':
                  // 流结束，但这通常在 final_result 之后
                  console.log('Stream completed');
                  break;
                  
                default:
                  console.log('Unknown event type:', data.event_type, data);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, line);
            }
          }
        }
      }
      
    } catch (error: unknown) {
      console.error('[CodeGenerationPage] Failed to generate code:', error);
      setIsGenerating(false);
      setShowProcessExplanation(false);
      
      const err = error as ApiError;
      let errorMessage = 'Code generation failed';
      
      if (typeof err === 'object' && err !== null && 'message' in err) {
        errorMessage = String(err.message);
      }
      
      // 提供基础模板
      const partialCode = `# Code generation failed, providing a basic template for reference
# Please modify the following code manually according to your SOP

from opentrons import protocol_api

metadata = {
    'protocolName': 'Generated Protocol Template',
    'author': 'LabScript AI',
    'description': 'Basic Protocol Template - Please modify according to your experimental needs',
    'apiLevel': '2.20'
}

def run(protocol: protocol_api.ProtocolContext):
    """
    Basic Protocol Template - Please modify according to your experimental needs
    """
    
    # 1. Load tip racks
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    
    # 2. Load pipette
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack_300])
    
    # 3. Load labware
    source_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 2)
    dest_plate = protocol.load_labware('nest_96_wellplate_200ul_flat', 3)
    
    # 4. Protocol Steps - Please modify according to your SOP
    # Example: Simple liquid transfer
    pipette.pick_up_tip()
    pipette.aspirate(100, source_plate['A1'])
    pipette.dispense(100, dest_plate['A1'])
    pipette.drop_tip()
    
    # TODO: Add specific experimental steps according to your SOP
    protocol.comment("Please add specific experimental steps according to your SOP")
`;
      
      const warningsToShow = ['A basic protocol template has been provided. Please modify it according to your SOP.'];
      
      // 设置代码和状态
      setEditedCode(partialCode);
      dispatch({ type: 'SET_PYTHON_CODE', payload: partialCode });
      setWarnings(warningsToShow);
      
      setProgress(`⚠️ ${errorMessage}, a basic template is provided for your reference`);
      enqueueSnackbar(errorMessage, { variant: 'error' });
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(editedCode || '');
    enqueueSnackbar('Code copied to clipboard', { variant: 'success' });
  };

  const handleEditorChange = (value: string | undefined) => {
    setEditedCode(value || '');
  };

  const handleRunSimulation = () => {
    dispatch({ type: 'SET_PYTHON_CODE', payload: editedCode });
    navigate('/simulation-results');
  };

  // Calculate code statistics
  const codeStats = {
    lines: editedCode ? editedCode.split('\n').length : 0,
    characters: editedCode ? editedCode.length : 0,
    generationTime: generationStartTime && !isGenerating 
      ? Math.round((Date.now() - generationStartTime.getTime()) / 1000) 
      : null
  };

  // 按尝试次数分组日志的处理函数
  const groupLogsByAttempt = (logs: IterationLog[]) => {
    const attemptGroups = new Map<number, IterationLog[]>();
    
    // 只处理有attempt_num的日志，忽略初始化等事件
    logs.forEach(log => {
      if (log.attempt_num && typeof log.attempt_num === 'number') {
        if (!attemptGroups.has(log.attempt_num)) {
          attemptGroups.set(log.attempt_num, []);
        }
        attemptGroups.get(log.attempt_num)!.push(log);
      }
    });
    
    // 转换为排序后的数组，每个元素包含 attemptNumber 和对应的日志
    return Array.from(attemptGroups.entries())
      .sort(([a], [b]) => a - b) // 按尝试次数排序
      .map(([attemptNum, attemptLogs]) => ({
        attemptNumber: attemptNum,
        logs: attemptLogs.sort((a, b) => {
          // 在单次尝试内，按时间戳排序
          const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
          const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
          return timeA - timeB;
        }),
        // 确定这次尝试的最终状态
        finalStatus: (() => {
          const finalResult = attemptLogs.find(log => log.event_type === 'attempt_result');
          if (finalResult && finalResult.status) {
            return finalResult.status;
          }
          // 如果没有attempt_result，从simulator的结果推断
          const simulatorResult = attemptLogs.find(log => 
            log.event_type === 'node_complete' && log.node_name === 'simulator'
          );
          if (simulatorResult) {
            if (simulatorResult.simulation_success) {
              return simulatorResult.has_warnings ? 'SUCCESS_WITH_WARNINGS' : 'SUCCESS';
            } else {
              return 'FAILED';
            }
          }
          return 'UNKNOWN';
        })()
      }));
  };

  // 获取分组后的日志
  const groupedLogs = groupLogsByAttempt(iterationLogs);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`,
        py: 4
      }}
    >
      <Container maxWidth="xl">
        {/* Header Section */}
        <Box sx={{ mb: 6, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            <Code2 size={32} color={theme.palette.primary.main} />
            <Typography 
              variant="h3" 
              component="h1" 
              sx={{ 
                fontWeight: 800, 
                ml: 2,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Generated Protocol Code
            </Typography>
          </Box>
          <Typography 
            variant="h6" 
            color="text.secondary" 
            sx={{ 
              maxWidth: 800, 
              mx: 'auto',
              lineHeight: 1.6,
              fontWeight: 400,
              mb: 2
            }}
          >
            AI-powered generation and validation of Opentrons Python protocol code, automatically optimized based on your SOP
          </Typography>
          
          {showReadyAlert && !editedCode && !isGenerating && (
            <Alert 
              severity="info" 
              onClose={() => setShowReadyAlert(false)}
              sx={{ 
                maxWidth: 600, 
                mx: 'auto',
                borderRadius: 2,
                '& .MuiAlert-message': {
                  textAlign: 'center',
                  fontSize: '0.9rem'
                }
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                🚀 Ready to Generate Your Custom Protocol Code
              </Typography>
              We will use advanced AI technology to analyze your SOP and generate verified, high-quality code.
              The entire process typically takes 2-5 minutes, please wait patiently.
            </Alert>
          )}
        </Box>
        
        {/* Upper Section: Controls and Code Editor */}
        <Grid container spacing={4} sx={{ mb: 6 }}>
          {/* Left Column: Controls and Status */}
          <Grid item xs={12} lg={4}>
            {/* Controls Card */}
            <Card 
              elevation={0}
              sx={{
                mb: 3,
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                    }}
                  >
                    <Zap size={24} color={theme.palette.primary.main} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Controls
                  </Typography>
                </Stack>
                
                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  onClick={handleGenerateCode} 
                  disabled={isGenerating}
                  startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <RefreshCw size={20} />}
                  sx={{ 
                    mb: 2,
                    py: 1.5,
                    borderRadius: 2,
                    fontWeight: 600,
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.3)}`,
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.4)}`,
                    },
                    '&:disabled': {
                      background: theme.palette.action.disabledBackground,
                      transform: 'none',
                      boxShadow: 'none',
                    }
                  }}
                >
                  {isGenerating ? 'Intelligent Generation...' : 'Start Code Generation'}
                </Button>
                
                <Button
                  fullWidth
                  variant="outlined"
                  size="large"
                  startIcon={<ArrowLeft />}
                  onClick={() => navigate('/define-sop')}
                  sx={{
                    py: 1.5,
                    borderRadius: 2,
                    fontWeight: 600,
                    borderColor: alpha(theme.palette.primary.main, 0.3),
                    color: theme.palette.primary.main,
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      borderColor: theme.palette.primary.main,
                      background: alpha(theme.palette.primary.main, 0.05),
                      transform: 'translateY(-1px)',
                    }
                  }}
                >
                  Back to SOP Editor
                </Button>
              </CardContent>
            </Card>

            {/* Process Explanation Card */}
            {(showProcessExplanation || isGenerating) && (
              <Card 
                elevation={0}
                sx={{
                  mb: 3,
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.05)} 0%, ${alpha(theme.palette.primary.main, 0.05)} 100%)`,
                  backdropFilter: 'blur(10px)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                      }}
                    >
                      <Info size={24} color={theme.palette.primary.main} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      Intelligent Code Generation Process
                    </Typography>
                  </Stack>
                  
                  <Alert 
                    severity="info" 
                    sx={{ 
                      mb: 3,
                      borderRadius: 2,
                      '& .MuiAlert-message': {
                        fontSize: '0.95rem',
                        lineHeight: 1.6,
                      }
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      💡 Estimated Time Required: {Math.ceil(getTotalEstimatedTime() / 60)} minutes
                    </Typography>
                    Our AI system will execute a multi-stage intelligent generation and validation process to ensure the generated code can run safely and accurately on Opentrons robots.
                    Please be patient, complex experiments may require multiple iterative optimizations.
                  </Alert>

                  <Stepper activeStep={currentStep} orientation="vertical">
                    {generationSteps.map((step, index) => (
                      <Step key={step.label}>
                        <StepLabel
                          StepIconComponent={({ active, completed }) => (
                            <Box
                              sx={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                background: completed 
                                  ? `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.light})`
                                  : active 
                                    ? `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.light})`
                                    : alpha(theme.palette.action.disabled, 0.1),
                                color: (completed || active) ? 'white' : theme.palette.text.disabled,
                                border: active ? `2px solid ${theme.palette.primary.main}` : 'none',
                                animation: active && isGenerating ? 'pulse 2s infinite' : 'none',
                                '@keyframes pulse': {
                                  '0%': {
                                    transform: 'scale(1)',
                                    boxShadow: `0 0 0 0 ${alpha(theme.palette.primary.main, 0.7)}`,
                                  },
                                  '50%': {
                                    transform: 'scale(1.05)',
                                    boxShadow: `0 0 0 10px ${alpha(theme.palette.primary.main, 0)}`,
                                  },
                                  '100%': {
                                    transform: 'scale(1)',
                                    boxShadow: `0 0 0 0 ${alpha(theme.palette.primary.main, 0)}`,
                                  },
                                },
                              }}
                            >
                              {completed ? <CheckCircle size={20} /> : step.icon}
                            </Box>
                          )}
                        >
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {step.label}
                          </Typography>
                        </StepLabel>
                        <StepContent>
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            sx={{ mb: 2, lineHeight: 1.6 }}
                          >
                            {step.description}
                          </Typography>
                          {index === currentStep && isGenerating && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <CircularProgress size={16} thickness={4} />
                              <Typography variant="caption" color="text.secondary">
                                Estimated {step.estimatedTime} seconds...
                              </Typography>
                            </Box>
                          )}
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>

                  {isGenerating && (
                    <Box sx={{ mt: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Overall Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {estimatedTime}s / {getTotalEstimatedTime()}s
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={(estimatedTime / getTotalEstimatedTime()) * 100}
                        sx={{
                          borderRadius: 1,
                          height: 8,
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 1,
                            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                          }
                        }}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 详细迭代过程已移动到页面底部 */}

            {/* Additional Generation Info Card */}
            {isGenerating && (
              <Card 
                elevation={0}
                sx={{
                  mb: 3,
                  borderRadius: 3,
                  border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                  background: `linear-gradient(135deg, ${alpha(theme.palette.info.light, 0.05)} 0%, ${alpha(theme.palette.info.main, 0.05)} 100%)`,
                  backdropFilter: 'blur(10px)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                    <Cpu size={24} color={theme.palette.info.main} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Backend Status
                    </Typography>
                  </Stack>
                  
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Current Status:
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500, mb: 2 }}>
                      {progress || 'Preparing generation environment...'}
                    </Typography>
                    
                    <List dense sx={{ py: 0 }}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <CheckCircle size={16} color={theme.palette.success.main} />
                        </ListItemIcon>
                        <ListItemText 
                          primary="SOP parsing completed" 
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {currentStep >= 1 ? (
                            <CheckCircle size={16} color={theme.palette.success.main} />
                          ) : (
                            <CircularProgress size={16} thickness={4} />
                          )}
                        </ListItemIcon>
                        <ListItemText 
                          primary="Code generation engine running" 
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {currentStep >= 2 ? (
                            <CheckCircle size={16} color={theme.palette.success.main} />
                          ) : (
                            <Clock size={16} color={theme.palette.text.disabled} />
                          )}
                        </ListItemIcon>
                        <ListItemText 
                          primary="Simulator validation" 
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {currentStep >= 3 ? (
                            <CheckCircle size={16} color={theme.palette.success.main} />
                          ) : (
                            <Clock size={16} color={theme.palette.text.disabled} />
                          )}
                        </ListItemIcon>
                        <ListItemText 
                          primary="Smart optimization iteration" 
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    </List>
                  </Box>
                  
                  <Alert severity="info" sx={{ borderRadius: 1 }}>
                    <Typography variant="caption">
                      💡 Tip: Complex experimental protocols may require more time for iterative optimization to ensure code accuracy and safety
                    </Typography>
                  </Alert>
                </CardContent>
              </Card>
            )}



            {/* Status and Statistics Card */}
            <Card 
              elevation={0}
              sx={{
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.success.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      background: `linear-gradient(45deg, ${alpha(theme.palette.success.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                    }}
                  >
                    {warnings.length > 0 ? (
                      <AlertTriangle size={24} color={theme.palette.warning.main} />
                    ) : editedCode ? (
                      <CheckCircle size={24} color={theme.palette.success.main} />
                    ) : (
                      <Clock size={24} color={theme.palette.info.main} />
                    )}
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Generation Status
                  </Typography>
                </Stack>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {progress || 'Ready to generate protocol code.'}
                </Typography>
                
                {editedCode && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                      Code Statistics
                    </Typography>
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Lines:</Typography>
                        <Chip label={codeStats.lines} size="small" color="primary" variant="outlined" />
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Characters:</Typography>
                        <Chip label={codeStats.characters.toLocaleString()} size="small" color="primary" variant="outlined" />
                      </Box>
                      {attempts > 0 && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Attempts:</Typography>
                          <Chip label={attempts} size="small" color="secondary" variant="outlined" />
                        </Box>
                      )}
                      {codeStats.generationTime && (
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">Generation Time:</Typography>
                          <Chip label={`${codeStats.generationTime}s`} size="small" color="success" variant="outlined" />
                        </Box>
                      )}
                    </Stack>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Right Column: Code Editor */}
          <Grid item xs={12} lg={8}>
            <Card 
              elevation={0}
              sx={{
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                      }}
                    >
                      <FileCode size={24} color={theme.palette.primary.main} />
                    </Box>
                    <Box>
                      <Typography variant="h6" component="h2" sx={{ fontWeight: 700 }}>
                        Protocol Python Code
                      </Typography>
                      {attempts > 0 && (
                        <Typography variant="body2" color="text.secondary">
                          Generated after {attempts} attempts
                        </Typography>
                      )}
                    </Box>
                  </Stack>
                  
                  <Tooltip title="Copy code to clipboard">
                    <Box component="span">
                      <IconButton 
                        onClick={handleCopyCode} 
                        color="primary" 
                        disabled={!editedCode}
                        sx={{
                          borderRadius: 2,
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            background: alpha(theme.palette.primary.main, 0.1),
                            transform: 'scale(1.1)',
                          }
                        }}
                      >
                        <Copy size={20} />
                      </IconButton>
                    </Box>
                  </Tooltip>
                </Box>
                
                <Paper
                  elevation={0}
                  sx={{ 
                    position: 'relative',
                    border: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    borderRadius: 2, 
                    overflow: 'hidden',
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      border: `2px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                    }
                  }}
                >
                  {isGenerating && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: alpha(theme.palette.background.paper, 0.8),
                        backdropFilter: 'blur(2px)',
                        zIndex: 10,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Stack alignItems="center" spacing={2}>
                        <CircularProgress size={60} />
                        <Typography variant="h6" color="text.primary">
                          AI is generating your protocol...
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                          This process may take 2-5 minutes. Please wait. You can switch to another page.
                        </Typography>
                      </Stack>
                    </Box>
                  )}
                  <Editor
                    height="800px"
                    defaultLanguage="python"
                    value={editedCode}
                    onChange={handleEditorChange}
                    options={{
                      theme: 'vs',
                      fontSize: 14,
                      minimap: { enabled: true },
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      readOnly: isGenerating,
                      lineNumbers: 'on',
                      folding: true,
                      wordWrap: 'on',
                      renderWhitespace: 'selection',
                    }}
                  />
                </Paper>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                endIcon={<Play />}
                onClick={handleRunSimulation}
                disabled={!editedCode || isGenerating}
                sx={{ 
                  py: 1.5, 
                  px: 4,
                  borderRadius: 2,
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  boxShadow: `0 6px 24px ${alpha(theme.palette.primary.main, 0.3)}`,
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-3px)',
                    boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.4)}`,
                  },
                  '&:disabled': {
                    background: theme.palette.action.disabledBackground,
                    transform: 'none',
                    boxShadow: 'none',
                  }
                }}
              >
                Run Simulation
              </Button>
            </Box>
          </Grid>
        </Grid>

        {/* Lower Section: Detailed Iteration Process (Full Width) */}
        {groupedLogs.length > 0 && !isGenerating && (
          <Box sx={{ mt: 6 }}>
            <Card 
              elevation={0}
              sx={{
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                background: `linear-gradient(135deg, ${alpha(theme.palette.info.light, 0.05)} 0%, ${alpha(theme.palette.info.main, 0.05)} 100%)`,
                backdropFilter: 'blur(10px)',
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                  <Cpu size={28} color={theme.palette.info.main} />
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Detailed Iteration Process
                  </Typography>
                  <Chip 
                    label={`${groupedLogs.length} Attempts`} 
                    size="medium" 
                    color="info" 
                    variant="outlined" 
                    sx={{ fontWeight: 600 }}
                  />
                </Stack>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4, fontSize: '1.1rem' }}>
                  The complete AI code generation iteration process: each attempt includes the full cycle of code generation → simulation validation → error analysis.
                </Typography>

                <Stack spacing={4}>
                  {groupedLogs.map((attemptGroup) => {
                    const isFailure = attemptGroup.finalStatus?.includes('FAILED');
                    const isSuccess = attemptGroup.finalStatus?.includes('SUCCESS');
                    
                    return (
                      <Accordion 
                        key={attemptGroup.attemptNumber}
                        elevation={0}
                        sx={{
                          border: `2px solid ${alpha(
                            isFailure ? theme.palette.error.main : 
                            isSuccess ? theme.palette.success.main : 
                            theme.palette.primary.main, 0.3
                          )}`,
                          borderRadius: 3,
                          '&:before': { display: 'none' },
                          background: alpha(
                            isFailure ? theme.palette.error.main : 
                            isSuccess ? theme.palette.success.main : 
                            theme.palette.primary.main, 0.05
                          ),
                        }}
                      >
                        <AccordionSummary
                          expandIcon={<Info size={24} />}
                          sx={{
                            '& .MuiAccordionSummary-content': {
                              alignItems: 'center',
                              gap: 2,
                              my: 1
                            }
                          }}
                        >
                          {/* 尝试次数和状态图标 */}
                          <Box
                            sx={{
                              p: 2,
                              borderRadius: 2,
                              background: alpha(
                                isFailure ? theme.palette.error.main : 
                                isSuccess ? theme.palette.success.main : 
                                theme.palette.primary.main, 0.15
                              ),
                            }}
                          >
                            {isFailure ? (
                              <AlertTriangle size={24} color={theme.palette.error.main} />
                            ) : isSuccess ? (
                              <CheckCircle size={24} color={theme.palette.success.main} />
                            ) : (
                              <RefreshCw size={24} color={theme.palette.primary.main} />
                            )}
                          </Box>
                          
                          {/* 尝试信息摘要 */}
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5 }}>
                              Attempt #{attemptGroup.attemptNumber}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Includes {attemptGroup.logs.length} processing steps • 
                              Status: {
                                attemptGroup.finalStatus === 'SUCCESS' ? 'Success' :
                                attemptGroup.finalStatus === 'SUCCESS_WITH_WARNINGS' ? 'Success (with warnings)' :
                                attemptGroup.finalStatus === 'FAILED' ? 'Validation Failed' :
                                attemptGroup.finalStatus === 'FINAL_FAILED' ? 'Final Failure' :
                                'Unknown'
                              }
                            </Typography>
                          </Box>
                          
                          {/* 状态标签 */}
                          <Chip
                            label={
                              attemptGroup.finalStatus === 'SUCCESS' ? '✅ Success' :
                              attemptGroup.finalStatus === 'SUCCESS_WITH_WARNINGS' ? '⚠️ Success (Warnings)' :
                              attemptGroup.finalStatus === 'FAILED' ? '❌ Failed' :
                              attemptGroup.finalStatus === 'FINAL_FAILED' ? '🔴 Final Failure' :
                              '❓ Unknown'
                            }
                            size="medium"
                            color={
                              isSuccess ? 'success' :
                              isFailure ? 'error' : 'default'
                            }
                            variant={isSuccess || isFailure ? 'filled' : 'outlined'}
                            sx={{ fontWeight: 600 }}
                          />
                        </AccordionSummary>
                        
                        <AccordionDetails sx={{ pt: 0, pb: 3 }}>
                          <Stack spacing={3}>
                            {/* 显示本次尝试的所有步骤 */}
                            {attemptGroup.logs.map((log, stepIndex) => (
                              <Paper 
                                key={stepIndex}
                                elevation={0}
                                sx={{
                                  p: 3,
                                  border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
                                  borderRadius: 2,
                                  borderLeft: `4px solid ${
                                    log.node_name === 'generator' ? theme.palette.primary.main :
                                    log.node_name === 'simulator' ? (log.simulation_success ? theme.palette.success.main : theme.palette.error.main) :
                                    log.node_name === 'feedback_preparer' ? theme.palette.warning.main :
                                    theme.palette.grey[400]
                                  }`
                                }}
                              >
                                <Stack spacing={2}>
                                  {/* 步骤标题 */}
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <Box
                                      sx={{
                                        p: 1,
                                        borderRadius: 1,
                                        background: alpha(
                                          log.node_name === 'generator' ? theme.palette.primary.main :
                                          log.node_name === 'simulator' ? (log.simulation_success ? theme.palette.success.main : theme.palette.error.main) :
                                          log.node_name === 'feedback_preparer' ? theme.palette.warning.main :
                                          theme.palette.grey[400], 0.15
                                        ),
                                      }}
                                    >
                                      {log.node_name === 'generator' ? (
                                        <Brain size={20} color={theme.palette.primary.main} />
                                      ) : log.node_name === 'simulator' ? (
                                        <TestTube size={20} color={log.simulation_success ? theme.palette.success.main : theme.palette.error.main} />
                                      ) : log.node_name === 'feedback_preparer' ? (
                                        <AlertTriangle size={20} color={theme.palette.warning.main} />
                                      ) : (
                                        <Cpu size={20} color={theme.palette.grey[600]} />
                                      )}
                                    </Box>
                                    <Box sx={{ flex: 1 }}>
                                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                        {log.node_name === 'generator' ? '🧠 AI Code Generation' :
                                         log.node_name === 'simulator' ? '🧪 Opentrons Simulation Validation' :
                                         log.node_name === 'feedback_preparer' ? '🔍 Error Analysis & Fix Strategy' :
                                         `📋 ${log.event_type}`}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        {log.message || (log.timestamp ? new Date(log.timestamp).toLocaleString() : '')}
                                      </Typography>
                                    </Box>
                                  </Box>

                                  {/* 步骤详细内容 */}
                                  {/* 模拟器错误详情 - 可折叠 */}
                                  {log.node_name === 'simulator' && !log.simulation_success && log.error_details && (
                                    <Accordion 
                                      elevation={0}
                                      sx={{
                                        border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                                        borderRadius: 1,
                                        '&:before': { display: 'none' },
                                        background: alpha(theme.palette.error.main, 0.05),
                                      }}
                                    >
                                      <AccordionSummary
                                        expandIcon={<Info size={16} />}
                                        sx={{ py: 1 }}
                                      >
                                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: theme.palette.error.main }}>
                                          🔴 Raw Error from Simulator (Click to expand)
                                        </Typography>
                                      </AccordionSummary>
                                      <AccordionDetails sx={{ pt: 0 }}>
                                        <Paper 
                                          elevation={0} 
                                          sx={{ 
                                            p: 2, 
                                            background: alpha(theme.palette.error.main, 0.08),
                                            border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
                                            borderRadius: 1
                                          }}
                                        >
                                          <Typography 
                                            variant="body2" 
                                            sx={{ 
                                              fontFamily: 'monospace', 
                                              whiteSpace: 'pre-wrap',
                                              fontSize: '0.85rem',
                                              color: theme.palette.error.dark,
                                              lineHeight: 1.4
                                            }}
                                          >
                                            {String(log.error_details)}
                                          </Typography>
                                        </Paper>
                                      </AccordionDetails>
                                    </Accordion>
                                  )}

                                  {/* AI错误分析 - 可折叠 */}
                                  {log.node_name === 'feedback_preparer' && log.error_analysis && (
                                    <Accordion 
                                      elevation={0}
                                      sx={{
                                        border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                                        borderRadius: 1,
                                        '&:before': { display: 'none' },
                                        background: alpha(theme.palette.primary.main, 0.05),
                                      }}
                                    >
                                      <AccordionSummary
                                        expandIcon={<Info size={16} />}
                                        sx={{ py: 1 }}
                                      >
                                        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
                                          🤖 AI's Error Analysis and Fix Plan (Click to expand)
                                        </Typography>
                                      </AccordionSummary>
                                      <AccordionDetails sx={{ pt: 0 }}>
                                        <Paper 
                                          elevation={0} 
                                          sx={{ 
                                            p: 3, 
                                            background: alpha(theme.palette.primary.main, 0.08),
                                            border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                                            borderRadius: 2
                                          }}
                                        >
                                          <Typography 
                                            variant="body2" 
                                            sx={{ 
                                              whiteSpace: 'pre-wrap',
                                              lineHeight: 1.6,
                                              color: theme.palette.primary.dark,
                                              fontSize: '0.9rem'
                                            }}
                                          >
                                            {String(log.error_analysis)}
                                          </Typography>
                                        </Paper>
                                      </AccordionDetails>
                                    </Accordion>
                                  )}

                                  {/* 代码生成成功信息 */}
                                  {log.node_name === 'generator' && log.has_code && (
                                    <Alert severity="info" sx={{ fontSize: '0.9rem' }}>
                                      ✅ Code generation complete, proceeding to simulation...
                                    </Alert>
                                  )}

                                  {/* 模拟成功但有警告 */}
                                  {log.node_name === 'simulator' && log.simulation_success && log.has_warnings && (
                                    <Alert severity="warning" sx={{ fontSize: '0.9rem' }}>
                                      ⚠️ Simulation passed, but with warnings. Please review.
                                    </Alert>
                                  )}

                                  {/* 模拟完全成功 */}
                                  {log.node_name === 'simulator' && log.simulation_success && !log.has_warnings && (
                                    <Alert severity="success" sx={{ fontSize: '0.9rem' }}>
                                      🎉 Simulation passed successfully! Code generation successful.
                                    </Alert>
                                  )}
                                </Stack>
                              </Paper>
                            ))}
                          </Stack>
                        </AccordionDetails>
                      </Accordion>
                    );
                  })}
                </Stack>
                
                {groupedLogs.length === 0 && (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <Cpu size={64} color={theme.palette.text.disabled} />
                    <Typography variant="h5" color="text.secondary" sx={{ mt: 3, mb: 2 }}>
                      No Iteration History
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      After starting code generation, the detailed AI thinking and fixing process will be displayed here.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default CodeGenerationPage;