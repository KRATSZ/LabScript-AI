import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container,
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Button,
  Divider,
  Paper,
  TextField,
  SelectChangeEvent,
  ToggleButton,
  ToggleButtonGroup,
  alpha,
  useTheme,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  Alert,
  DialogActions,
  Stack,
  Chip,
  Tooltip,
  IconButton,
  CircularProgress,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import { ArrowRight, Text, Layout, Settings, Notebook as Robot, HardDrive, Cpu, Zap, Wrench, Info } from 'lucide-react';
import { useAppContext, AppState, LabwareItem, PipetteModel } from '../context/AppContext';
import DeckLayout from '../components/hardware/DeckLayout';
import LabwareLibrary from '../components/hardware/LabwareLibrary';
import { formatHardwareConfig, apiService, PyLabRobotProfile } from '../services/api';
import { useSnackbar } from 'notistack';
import { hardwareTemplates } from '../utils/hardwareTemplates';

const STORAGE_KEY = 'labscript_hardware_config';

const apiVersions = ['2.18', '2.19', '2.20', '2.21'];

const LEGACY_DEFAULT_FLEX_CONFIG = `Robot Model: Flex
API Version: 2.20
Left Pipette: None
Right Pipette: None
Use Gripper: false
Deck Layout:
  (No labware configured)`;

const flexPipettes = [
  { value: 'flex_1channel_1000', label: 'Flex 1-channel 1000µL' },
  { value: 'flex_1channel_300', label: 'Flex 1-channel 300µL' },
  { value: 'flex_8channel_1000', label: 'Flex 8-channel 1000µL' },
  { value: 'flex_8channel_300', label: 'Flex 8-channel 300µL' },
];

const ot2Pipettes = [
  { value: 'p1000_single_gen2', label: 'P1000 Single-Channel GEN2' },
  { value: 'p300_single_gen2', label: 'P300 Single-Channel GEN2' },
  { value: 'p20_single_gen2', label: 'P20 Single-Channel GEN2' },
  { value: 'p300_multi_gen2', label: 'P300 Multi-Channel GEN2' },
  { value: 'p20_multi_gen2', label: 'P20 Multi-Channel GEN2' },
];

const pyLabRobotPipettes = [
  { value: 'pylabrobot_1000', label: 'PyLabRobot 1000µL' },
  { value: 'pylabrobot_300', label: 'PyLabRobot 300µL' },
  { value: 'pylabrobot_50', label: 'PyLabRobot 50µL' },
];

const isLegacyDefaultFlexState = (state: AppState): boolean => (
  state.robotModel === 'Flex' &&
  state.apiVersion === '2.20' &&
  state.leftPipette === null &&
  state.rightPipette === null &&
  state.useGripper === false &&
  Object.values(state.deckLayout).every((labware) => labware === null)
);

const getTextConfigForState = (state: AppState): string => {
  if (isLegacyDefaultFlexState(state)) {
    return hardwareTemplates.Flex;
  }

  return formatHardwareConfig(state);
};

const normalizeRawHardwareConfigText = (rawConfig: string | null | undefined): string | null => {
  if (!rawConfig?.trim()) {
    return null;
  }

  return rawConfig.trim() === LEGACY_DEFAULT_FLEX_CONFIG ? hardwareTemplates.Flex : rawConfig;
};

// Helper to format JSON into a YAML-like string
const formatJsonToYamlStyle = (obj: any): string => {
  const yamlLines: string[] = [];
  
  const processObject = (currentObj: any, indentLevel: number) => {
    for (const key in currentObj) {
      if (Object.prototype.hasOwnProperty.call(currentObj, key)) {
        const value = currentObj[key];
        const indent = '  '.repeat(indentLevel);

        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          yamlLines.push(`${indent}${key}:`);
          processObject(value, indentLevel + 1);
        } else if (Array.isArray(value)) {
          yamlLines.push(`${indent}${key}:`);
          value.forEach(item => {
            if (typeof item === 'object' && item !== null) {
              // For arrays of objects, currently just stringify them
              yamlLines.push(`${indent}  - ${JSON.stringify(item)}`);
            } else {
              yamlLines.push(`${indent}  - ${item}`);
            }
          });
        } else {
          yamlLines.push(`${indent}${key}: ${value}`);
        }
      }
    }
  };

  processObject(obj, 0);
  return yamlLines.join('\n');
};


const HardwareConfigPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const [configMode, setConfigMode] = useState<'text' | 'visual'>('text');
  const [configText, setConfigText] = useState('');
  const [showConfig, setShowConfig] = useState(Boolean(state.robotModel));
  const [showDevDialog, setShowDevDialog] = useState(false);
  const [showPyLabRobotDialog, setShowPyLabRobotDialog] = useState(false);
  const [pyLabRobotProfiles, setPyLabRobotProfiles] = useState<PyLabRobotProfile[]>([]);
  const [loadingProfiles, setLoadingProfiles] = useState(false);
  const [selectedPyLabRobotProfile, setSelectedPyLabRobotProfile] = useState<string>('');
  const { enqueueSnackbar } = useSnackbar();
  
  const shouldShowModeToggle = state.robotModel !== 'PyLabRobot';
  const effectiveConfigMode = state.robotModel === 'PyLabRobot' ? 'text' : configMode;
  
  useEffect(() => {
    const savedConfig = localStorage.getItem(STORAGE_KEY);
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig);
        const rawHardwareConfigText = normalizeRawHardwareConfigText(config.rawHardwareConfigText);
        dispatch({ type: 'SET_ROBOT_MODEL', payload: config.robotModel });
        dispatch({ type: 'SET_API_VERSION', payload: config.apiVersion });
        dispatch({ type: 'SET_LEFT_PIPETTE', payload: config.leftPipette });
        dispatch({ type: 'SET_RIGHT_PIPETTE', payload: config.rightPipette });
        dispatch({ type: 'SET_USE_GRIPPER', payload: config.useGripper });
        dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: rawHardwareConfigText });

        Object.entries(config.deckLayout || {}).forEach(([slot, labware]) => {
          dispatch({ 
            type: 'SET_DECK_LABWARE', 
            payload: { slot, labware: labware as LabwareItem | null } 
          });
        });
        
        setShowConfig(true);
        if (rawHardwareConfigText) {
          setConfigText(rawHardwareConfigText);
          setConfigMode('text');
        } else {
          setConfigMode('visual'); 
        }

      } catch (error) {
        console.error('Error loading saved configuration:', error);
        enqueueSnackbar('Error loading saved configuration', { variant: 'error' });
      }
    }
  }, [dispatch, enqueueSnackbar]);

  const getPipetteOptions = () => {
    switch (state.robotModel) {
      case 'Flex':
        return flexPipettes;
      case 'OT-2':
        return ot2Pipettes;
      case 'PyLabRobot':
        return pyLabRobotPipettes;
      default:
        return [];
    }
  };

  const pipetteOptions = getPipetteOptions();
  
  const handleConfigModeChange = (_: React.MouseEvent<HTMLElement>, newMode: 'text' | 'visual') => {
    if (newMode !== null) {
      setConfigMode(newMode);
      if (newMode === 'visual') {
        dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: null });
        enqueueSnackbar('Visual Configuration is currently in development and may contain bugs.', { 
          variant: 'warning',
          autoHideDuration: 5000,
          anchorOrigin: { vertical: 'top', horizontal: 'center' }
        });
      } else {
        setConfigText(getTextConfigForState(state));
      }
    }
  };

  // Load PyLabRobot profiles
  const loadPyLabRobotProfiles = async () => {
    setLoadingProfiles(true);
    try {
      const response = await apiService.getPyLabRobotProfiles();
      if (response.success) {
        setPyLabRobotProfiles(response.profiles);
      } else {
        enqueueSnackbar('Failed to load PyLabRobot profiles', { variant: 'error' });
      }
    } catch (error) {
      console.error('Error loading PyLabRobot profiles:', error);
      enqueueSnackbar('Error loading PyLabRobot profiles', { variant: 'error' });
    } finally {
      setLoadingProfiles(false);
    }
  };

  // Handle PyLabRobot profile selection
  const handlePyLabRobotProfileSelect = (profile: PyLabRobotProfile) => {
    setSelectedPyLabRobotProfile(profile.robot_model);
    
    // Format the profile's default_config into a user-friendly, YAML-like string
    const profileConfig = formatJsonToYamlStyle(profile.default_config);

    setConfigText(profileConfig);
    dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: profileConfig });
    dispatch({ type: 'SET_ROBOT_MODEL', payload: 'PyLabRobot' });
    
    // Reset pipette settings for PyLabRobot
    dispatch({ type: 'SET_LEFT_PIPETTE', payload: null });
    dispatch({ type: 'SET_RIGHT_PIPETTE', payload: null });
    dispatch({ type: 'SET_USE_GRIPPER', payload: false });
    
    // Clear deck layout
    Object.keys(state.deckLayout).forEach(slot => {
      dispatch({
        type: 'SET_DECK_LABWARE',
        payload: { slot, labware: null }
      });
    });

    setConfigMode('text');
    setShowConfig(true);
    setShowPyLabRobotDialog(false);
    
    enqueueSnackbar(`Selected ${profile.display_name} configuration`, { variant: 'success' });
  };

  const handleRobotModelChange = (event: SelectChangeEvent<string>) => {
    const model = event.target.value as 'Flex' | 'OT-2' | 'PyLabRobot';
    if (model === 'PyLabRobot') {
      // First show experimental warning, then device selection
      setShowDevDialog(true);
      return;
    }
    
    dispatch({ type: 'SET_ROBOT_MODEL', payload: model });
    
    // Reset core components
    dispatch({ type: 'SET_LEFT_PIPETTE', payload: null });
    dispatch({ type: 'SET_RIGHT_PIPETTE', payload: null });
    dispatch({ type: 'SET_USE_GRIPPER', payload: false });

    // Clear the entire deck layout to prevent state pollution
    Object.keys(state.deckLayout).forEach(slot => {
      dispatch({
        type: 'SET_DECK_LABWARE',
        payload: { slot, labware: null }
      });
    });

    // Load the default text configuration for the selected model
    const template = hardwareTemplates[model] || '';
    setConfigText(template);
    
    // Ensure raw config text is cleared if we are in visual mode,
    // or updated if we are in text mode.
    if (configMode === 'text') {
      dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: template });
    } else {
      dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: null });
    }

    setShowConfig(true);
  };

  const handleApiVersionChange = (event: SelectChangeEvent<string>) => {
    dispatch({ type: 'SET_API_VERSION', payload: event.target.value });
  };

  const handleLeftPipetteChange = (event: SelectChangeEvent<string>) => {
    dispatch({ 
      type: 'SET_LEFT_PIPETTE', 
      payload: event.target.value === 'none' ? null : event.target.value as PipetteModel
    });
  };

  const handleRightPipetteChange = (event: SelectChangeEvent<string>) => {
    dispatch({ 
      type: 'SET_RIGHT_PIPETTE', 
      payload: event.target.value === 'none' ? null : event.target.value as PipetteModel
    });
  };

  const handleGripperChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch({ type: 'SET_USE_GRIPPER', payload: event.target.checked });
  };

  const handleConfigTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setConfigText(event.target.value);
  };

  const saveConfiguration = () => {
    const configToSave = {
      robotModel: state.robotModel,
      apiVersion: state.apiVersion,
      leftPipette: state.leftPipette,
      rightPipette: state.rightPipette,
      useGripper: state.useGripper,
      deckLayout: state.deckLayout,
      rawHardwareConfigText: configMode === 'text' ? configText : null,
    };
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(configToSave));
    enqueueSnackbar('Configuration saved successfully!', { variant: 'success' });
  };

  const handleSaveAndContinue = () => {
    if (effectiveConfigMode === 'text') {
      if (configText.trim() !== '') {
        dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: configText });
      } else {
        dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: null }); 
        enqueueSnackbar('Text configuration is empty. Visual configuration (if set) or defaults will be used.', { variant: 'info' });
      }
    } else {
        dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: null });
    }
    saveConfiguration(); 
    navigate('/define-sop');
  };

  const isConfigValid = effectiveConfigMode === 'text' 
    ? Boolean(configText.trim()) 
    : Boolean(state.robotModel && (state.leftPipette || state.rightPipette || (state.robotModel === 'Flex' && state.useGripper)));

  useEffect(() => {
    document.title = 'Configure Hardware - LabScript AI';
    if (state.robotModel) { 
      setShowConfig(true);
    }
    if (effectiveConfigMode === 'text' && !state.rawHardwareConfigText) {
      setConfigText(getTextConfigForState(state));
    } else if (effectiveConfigMode === 'text' && state.rawHardwareConfigText) {
      setConfigText(state.rawHardwareConfigText);
    }
  }, [state.robotModel, state.apiVersion, state.leftPipette, state.rightPipette, state.useGripper, state.deckLayout, effectiveConfigMode, state.rawHardwareConfigText]);

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
            <HardDrive size={32} color={theme.palette.primary.main} />
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
              Configure Your Lab Hardware
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
            Set up your Opentrons robot configuration, pipettes, and define the labware on your deck for optimal protocol execution
          </Typography>
        </Box>

        {/* Robot Model Selection */}
        <Card 
          elevation={0}
          sx={{ 
            mb: 4,
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
          <CardContent sx={{ p: 4 }}>
            <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
              <Box
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                }}
              >
                <Robot size={24} color={theme.palette.primary.main} />
              </Box>
              <Box>
                <Typography variant="h5" component="h2" sx={{ fontWeight: 700, mb: 0.5 }}>
                  Select Robot Model
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose your Opentrons robot model to begin configuration
                </Typography>
              </Box>
            </Stack>
            
            <FormControl 
              fullWidth 
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.15)}`,
                  },
                  '&.Mui-focused': {
                    boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.25)}`,
                  }
                }
              }}
            >
              <InputLabel id="robot-model-label">Robot Model</InputLabel>
              <Select
                labelId="robot-model-label"
                id="robot-model"
                value={state.robotModel}
                label="Robot Model"
                onChange={handleRobotModelChange}
                sx={{ py: 1 }}
              >
                <MenuItem value="Flex">
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Zap size={20} color={theme.palette.primary.main} />
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>Opentrons Flex</Typography>
                      <Typography variant="caption" color="text.secondary">Latest generation robot</Typography>
                    </Box>
                  </Stack>
                </MenuItem>
                <MenuItem value="OT-2">
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Cpu size={20} color={theme.palette.info.main} />
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>Opentrons OT-2</Typography>
                      <Typography variant="caption" color="text.secondary">Reliable and proven platform</Typography>
                    </Box>
                  </Stack>
                </MenuItem>
                <MenuItem value="PyLabRobot">
                  <Stack direction="row" alignItems="center" spacing={2}>
                    <Settings size={20} color={theme.palette.warning.main} />
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>PyLabRobot</Typography>
                      <Typography variant="caption" color="text.secondary">Experimental platform</Typography>
                    </Box>
                    <Chip label="BETA" size="small" color="warning" variant="outlined" />
                  </Stack>
                </MenuItem>
              </Select>
            </FormControl>
          </CardContent>
        </Card>

        {/* PyLabRobot Experimental Dialog */}
        <Dialog 
          open={showDevDialog} 
          onClose={() => setShowDevDialog(false)}
          PaperProps={{
            sx: {
              borderRadius: 3,
              boxShadow: `0 24px 48px ${alpha(theme.palette.common.black, 0.12)}`,
            }
          }}
        >
          <DialogTitle sx={{ pb: 2 }}>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Settings size={24} color={theme.palette.warning.main} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                PyLabRobot - Experimental Feature
              </Typography>
            </Stack>
          </DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2, borderRadius: 2 }}>
              <Typography variant="body2">
                ⚠️ PyLabRobot features are currently under testing and have incomplete functionality. Use with caution.
              </Typography>
            </Alert>
            <DialogContentText>
              <Typography variant="body1" sx={{ mb: 2 }}>
                <strong>Current Status:</strong> This platform is in active development with the following limitations:
              </Typography>
              <Typography variant="body2" component="ul" sx={{ pl: 2, mb: 2 }}>
                <li>Code generation may require multiple attempts</li>
                <li>Some PyLabRobot features may not be fully supported</li>
                <li>Simulation accuracy is limited</li>
                <li>Protocol validation is experimental</li>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                For production workflows, we strongly recommend using Opentrons Flex or OT-2 platforms.
              </Typography>
            </DialogContentText>
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button 
              onClick={() => {
                setShowDevDialog(false);
                // Force re-render of the select component to reset to current state
                const currentSelect = document.getElementById('robot-model') as HTMLSelectElement;
                if (currentSelect) {
                  currentSelect.value = state.robotModel || '';
                }
              }} 
              variant="contained"
            >
              OK
            </Button>
          </DialogActions>
        </Dialog>

        {/* PyLabRobot Device Selection Dialog */}
        <Dialog 
          open={showPyLabRobotDialog} 
          onClose={() => setShowPyLabRobotDialog(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: {
              borderRadius: 3,
              boxShadow: `0 24px 48px ${alpha(theme.palette.common.black, 0.12)}`,
            }
          }}
        >
          <DialogTitle sx={{ pb: 2 }}>
            <Stack direction="row" alignItems="center" spacing={2}>
              <Settings size={24} color={theme.palette.primary.main} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Select PyLabRobot Device
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Choose a specific robot model for optimized protocol generation
                </Typography>
              </Box>
            </Stack>
          </DialogTitle>
          <DialogContent>
            {loadingProfiles ? (
              <Box display="flex" justifyContent="center" alignItems="center" py={4}>
                <CircularProgress />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  Loading available robot configurations...
                </Typography>
              </Box>
            ) : pyLabRobotProfiles.length === 0 ? (
              <Alert severity="info" sx={{ borderRadius: 2 }}>
                <Typography variant="body2">
                  No PyLabRobot configurations found. Please check your backend configuration.
                </Typography>
              </Alert>
            ) : (
              <Box>
                <Alert severity="info" sx={{ mb: 3, borderRadius: 2 }}>
                  <Typography variant="body2">
                    Selecting a specific device model will optimize the AI agent for that platform's capabilities and best practices.
                  </Typography>
                </Alert>
                
                <Grid container spacing={2}>
                  {pyLabRobotProfiles.map((profile) => (
                    <Grid item xs={12} sm={6} key={profile.robot_model} sx={{ display: 'flex' }}>
                      <Card 
                        variant="outlined"
                        sx={{
                          height: '100%',
                          cursor: 'pointer',
                          transition: 'all 0.3s ease-in-out',
                          border: selectedPyLabRobotProfile === profile.robot_model 
                            ? `2px solid ${theme.palette.primary.main}` 
                            : `1px solid ${alpha(theme.palette.divider, 0.2)}`,
                          '&:hover': {
                            boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
                            transform: 'translateY(-2px)',
                          }
                        }}
                        onClick={() => setSelectedPyLabRobotProfile(profile.robot_model)}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Stack direction="row" alignItems="flex-start" spacing={2}>
                            <Box
                              sx={{
                                p: 1,
                                borderRadius: 1,
                                background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                              }}
                            >
                              <Robot size={20} color={theme.palette.primary.main} />
                            </Box>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                                <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
                                  {profile.display_name}
                                </Typography>
                                <Chip 
                                  label={profile.precision_class} 
                                  size="small" 
                                  color={profile.precision_class === 'high' ? 'success' : 'default'}
                                  variant="outlined"
                                />
                              </Stack>
                              
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {profile.manufacturer}
                              </Typography>
                              
                              <Typography variant="body2" sx={{ mb: 1, fontSize: '0.875rem' }}>
                                {profile.description}
                              </Typography>
                              
                              <Typography variant="caption" color="text.secondary">
                                Volume: {profile.volume_range.min_ul}µL - {profile.volume_range.max_ul}µL
                              </Typography>
                              
                              {profile.special_features.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                                    Features:
                                  </Typography>
                                  <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
                                    {profile.special_features.slice(0, 3).map((feature, index) => (
                                      <Chip 
                                        key={index}
                                        label={feature} 
                                        size="small" 
                                        variant="outlined"
                                        sx={{ fontSize: '0.7rem', height: 'auto', py: 0.25 }}
                                      />
                                    ))}
                                    {profile.special_features.length > 3 && (
                                      <Chip 
                                        label={`+${profile.special_features.length - 3} more`}
                                        size="small" 
                                        variant="outlined"
                                        sx={{ fontSize: '0.7rem', height: 'auto', py: 0.25 }}
                                      />
                                    )}
                                  </Stack>
                                </Box>
                              )}
                            </Box>
                          </Stack>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setShowPyLabRobotDialog(false)} variant="outlined">
              Cancel
            </Button>
            <Button 
              onClick={() => {
                const selectedProfile = pyLabRobotProfiles.find(p => p.robot_model === selectedPyLabRobotProfile);
                if (selectedProfile) {
                  handlePyLabRobotProfileSelect(selectedProfile);
                }
              }}
              variant="contained"
              disabled={!selectedPyLabRobotProfile || loadingProfiles}
            >
              Select Device
            </Button>
          </DialogActions>
        </Dialog>

        {/* Configuration Mode Toggle */}
        {showConfig && shouldShowModeToggle && (
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 1,
                borderRadius: 3,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                background: alpha(theme.palette.background.paper, 0.8),
                backdropFilter: 'blur(10px)',
              }}
            >
              <ToggleButtonGroup
                value={configMode}
                exclusive
                onChange={handleConfigModeChange}
                aria-label="Configuration Mode"
                sx={{
                  '& .MuiToggleButton-root': {
                    borderRadius: 2,
                    border: 'none',
                    px: 3,
                    py: 1.5,
                    fontWeight: 600,
                    transition: 'all 0.3s ease-in-out',
                    '&.Mui-selected': {
                      background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                      color: 'white',
                      '&:hover': {
                        background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.secondary.dark})`,
                      }
                    },
                    '&:hover': {
                      background: alpha(theme.palette.primary.main, 0.1),
                    }
                  }
                }}
              >
                <ToggleButton value="visual" aria-label="Visual Configuration">
                  <Layout style={{ marginRight: 8 }} />
                  Visual Configuration
                </ToggleButton>
                <ToggleButton value="text" aria-label="Text-based Configuration">
                  <Text style={{ marginRight: 8 }} />
                  Advanced Text Config
                </ToggleButton>
              </ToggleButtonGroup>
            </Paper>
          </Box>
        )}

        {/* Robot Configuration Section - New Position */}
        {showConfig && effectiveConfigMode === 'visual' && (
          <Card 
            elevation={0}
            sx={{
              mb: 4,
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
            <CardContent sx={{ p: 4 }}>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                  }}
                >
                  <Wrench size={24} color={theme.palette.primary.main} />
                </Box>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 700 }}>
                  Robot Configuration
                </Typography>
              </Stack>
              
              <Divider sx={{ my: 3 }} />

              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <FormControl 
                    fullWidth 
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.1)}`,
                        }
                      }
                    }}
                  >
                    <InputLabel id="api-version-label">API Version (PAPI)</InputLabel>
                    <Select
                      labelId="api-version-label"
                      value={state.apiVersion}
                      label="API Version (PAPI)"
                      onChange={handleApiVersionChange}
                    >
                      {apiVersions.map((version) => (
                        <MenuItem key={version} value={version}>
                          <Stack direction="row" alignItems="center" spacing={2}>
                            <Typography variant="body1">{version}</Typography>
                            {version === '2.21' && (
                              <Chip label="Latest" size="small" color="success" variant="outlined" />
                            )}
                          </Stack>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={3}>
                  <FormControl 
                    fullWidth 
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.1)}`,
                        }
                      }
                    }}
                  >
                    <InputLabel id="left-pipette-label">Left Pipette</InputLabel>
                    <Select
                      labelId="left-pipette-label"
                      value={state.leftPipette || 'none'}
                      label="Left Pipette"
                      onChange={handleLeftPipetteChange}
                      disabled={!pipetteOptions.length}
                    >
                      <MenuItem value="none">
                        <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>None</Typography>
                      </MenuItem>
                      {pipetteOptions.map((pipette) => (
                        <MenuItem key={pipette.value} value={pipette.value}>
                          {pipette.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {!pipetteOptions.length && state.robotModel && (
                      <Typography variant="caption" color="text.secondary" sx={{mt:1}}>
                        Select a robot model to see pipette options.
                      </Typography>
                    )}
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={3}>
                  <FormControl 
                    fullWidth 
                    variant="outlined"
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        transition: 'all 0.3s ease-in-out',
                        '&:hover': {
                          boxShadow: `0 2px 8px ${alpha(theme.palette.primary.main, 0.1)}`,
                        }
                      }
                    }}
                  >
                    <InputLabel id="right-pipette-label">Right Pipette</InputLabel>
                    <Select
                      labelId="right-pipette-label"
                      value={state.rightPipette || 'none'}
                      label="Right Pipette"
                      onChange={handleRightPipetteChange}
                      disabled={!pipetteOptions.length}
                    >
                      <MenuItem value="none">
                        <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>None</Typography>
                      </MenuItem>
                      {pipetteOptions.map((pipette) => (
                        <MenuItem key={pipette.value} value={pipette.value}>
                          {pipette.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {!pipetteOptions.length && state.robotModel && (
                      <Typography variant="caption" color="text.secondary" sx={{mt:1}}>
                        Select a robot model to see pipette options.
                      </Typography>
                    )}
                  </FormControl>
                </Grid>

                {state.robotModel === 'Flex' && (
                  <Grid item xs={12} md={3}>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                        background: alpha(theme.palette.info.light, 0.05),
                        height: '56px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <FormControlLabel
                        control={
                          <Switch 
                            checked={state.useGripper} 
                            onChange={handleGripperChange}
                            sx={{
                              '& .MuiSwitch-switchBase.Mui-checked': {
                                color: theme.palette.success.main,
                                '& + .MuiSwitch-track': {
                                  backgroundColor: theme.palette.success.main,
                                },
                              },
                            }}
                          />
                        }
                        label={
                          <Stack direction="row" alignItems="center" spacing={1}>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              Enable Gripper
                            </Typography>
                            <Tooltip title="The gripper allows automated handling of labware and plates">
                              <IconButton size="small">
                                <Info size={16} />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        }
                      />
                    </Box>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Main Content Area - New Layout */}
        {showConfig && effectiveConfigMode === 'visual' && (
          <Grid container spacing={4}>
            {/* Left Column: Labware Library */}
            <Grid item xs={12} lg={5}>
              <LabwareLibrary />
            </Grid>

            {/* Right Column: Deck Layout */}
            <Grid item xs={12} lg={7}>
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
                <CardContent sx={{ p: 4 }}>
                  <DeckLayout />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Text-based Configuration Area */}
        {showConfig && effectiveConfigMode === 'text' && (
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
            <CardContent sx={{ p: 4 }}>
              <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    background: `linear-gradient(45deg, ${alpha(theme.palette.warning.main, 0.1)}, ${alpha(theme.palette.info.main, 0.1)})`,
                  }}
                >
                  <Text size={24} color={theme.palette.warning.main} />
                </Box>
                <Box>
                  <Typography variant="h6" component="h3" sx={{ fontWeight: 700 }}>
                    Advanced Text Configuration
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Define your hardware setup using JSON format for maximum flexibility
                  </Typography>
                </Box>
              </Stack>
              
              <TextField
                multiline
                rows={15}
                fullWidth
                variant="outlined"
                placeholder={hardwareTemplates[state.robotModel] || getTextConfigForState(state)}
                value={configText}
                onChange={handleConfigTextChange}
                sx={{ 
                  fontFamily: 'monospace',
                  '& .MuiInputBase-root': {
                    borderRadius: 2,
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                      boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.1)}`,
                    },
                    '&.Mui-focused': {
                      boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.25)}`,
                    }
                  },
                  '& .MuiInputBase-input': {
                    fontSize: '0.875rem',
                    lineHeight: 1.6,
                    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                  }
                }}
              />
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        {showConfig && (
          <Box sx={{ mt: 6, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              variant="contained" 
              color="primary" 
              size="large"
              endIcon={<ArrowRight />}
              onClick={handleSaveAndContinue}
              disabled={!isConfigValid}
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
              Save Configuration & Continue
            </Button>
          </Box>
        )}
      </Container>
    </Box>
  );
};

export default HardwareConfigPage;
