import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Switch,
  FormControlLabel,
  Container,
  Alert,
  TextField,
  Tabs,
  Tab,
  Snackbar
} from '@mui/material';
import { useAppContext, RobotModel, PipetteModel, LabwareItem } from '../context/AppContext';
import { ChevronRight, ArrowLeft, Save } from 'lucide-react';
import { useSnackbar } from 'notistack';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const HardwareConfigPage: React.FC = () => {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const { enqueueSnackbar } = useSnackbar();
  const [tabValue, setTabValue] = useState(0);
  const [rawConfigText, setRawConfigText] = useState(state.rawHardwareConfigText || '');

  const robotModels: RobotModel[] = ['Flex', 'OT-2', 'PyLabRobot'];
  const apiVersions = ['2.20', '2.19', '2.18', '2.17', '2.16', '2.15'];

  const pipetteOptions: Record<RobotModel, PipetteModel[]> = {
    'Flex': ['flex_1channel_1000', 'flex_1channel_300', 'flex_8channel_1000', 'flex_8channel_300'],
    'OT-2': ['p1000_single_gen2', 'p300_single_gen2', 'p20_single_gen2', 'p1000_multi_gen2', 'p300_multi_gen2', 'p20_multi_gen2'],
    'PyLabRobot': ['pylabrobot_1000', 'pylabrobot_300', 'pylabrobot_50']
  };

  const commonLabware = [
    { type: 'tiprack', name: 'opentrons_96_tiprack_1000ul', displayName: '1000μL Tip Rack' },
    { type: 'tiprack', name: 'opentrons_96_tiprack_300ul', displayName: '300μL Tip Rack' },
    { type: 'plate', name: 'corning_96_wellplate_360ul_flat', displayName: '96-well Plate' },
    { type: 'reservoir', name: 'nest_12_reservoir_15ml', displayName: '12-well Reservoir' },
    { type: 'tuberack', name: 'opentrons_24_tuberack_nest_1.5ml_snapcap', displayName: '24-tube Rack' }
  ];

  const getDeckSlots = (robotModel: RobotModel) => {
    switch (robotModel) {
      case 'Flex':
        return ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'];
      case 'OT-2':
        return ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11'];
      case 'PyLabRobot':
        return ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12'];
      default:
        return [];
    }
  };

  const handleRobotModelChange = (model: RobotModel) => {
    dispatch({ type: 'SET_ROBOT_MODEL', payload: model });
  };

  const handleApiVersionChange = (version: string) => {
    dispatch({ type: 'SET_API_VERSION', payload: version });
  };

  const handleLeftPipetteChange = (pipette: PipetteModel) => {
    dispatch({ type: 'SET_LEFT_PIPETTE', payload: pipette });
  };

  const handleRightPipetteChange = (pipette: PipetteModel) => {
    dispatch({ type: 'SET_RIGHT_PIPETTE', payload: pipette });
  };

  const handleGripperChange = (useGripper: boolean) => {
    dispatch({ type: 'SET_USE_GRIPPER', payload: useGripper });
  };

  const handleLabwareChange = (slot: string, labware: LabwareItem | null) => {
    dispatch({ type: 'SET_DECK_LABWARE', payload: { slot, labware } });
  };

  const handleSaveConfiguration = () => {
    // Save raw config text if in text mode
    if (tabValue === 1) {
      dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: rawConfigText });
    } else {
      dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: null });
    }
    
    // Save to localStorage
    const configData = {
      robotModel: state.robotModel,
      apiVersion: state.apiVersion,
      leftPipette: state.leftPipette,
      rightPipette: state.rightPipette,
      useGripper: state.useGripper,
      deckLayout: state.deckLayout,
      rawHardwareConfigText: tabValue === 1 ? rawConfigText : null
    };
    localStorage.setItem('hardwareConfig', JSON.stringify(configData));
    
    enqueueSnackbar('Hardware configuration saved successfully!', { variant: 'success' });
  };

  const handleNext = () => {
    handleSaveConfiguration();
    navigate('/define-sop');
  };

  const handleBack = () => {
    navigate('/');
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Load configuration from localStorage on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('hardwareConfig');
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig);
        if (config.robotModel) dispatch({ type: 'SET_ROBOT_MODEL', payload: config.robotModel });
        if (config.apiVersion) dispatch({ type: 'SET_API_VERSION', payload: config.apiVersion });
        if (config.leftPipette !== undefined) dispatch({ type: 'SET_LEFT_PIPETTE', payload: config.leftPipette });
        if (config.rightPipette !== undefined) dispatch({ type: 'SET_RIGHT_PIPETTE', payload: config.rightPipette });
        if (config.useGripper !== undefined) dispatch({ type: 'SET_USE_GRIPPER', payload: config.useGripper });
        if (config.deckLayout) {
          Object.entries(config.deckLayout).forEach(([slot, labware]) => {
            dispatch({ type: 'SET_DECK_LABWARE', payload: { slot, labware: labware as LabwareItem | null } });
          });
        }
        if (config.rawHardwareConfigText) {
          setRawConfigText(config.rawHardwareConfigText);
          dispatch({ type: 'SET_RAW_HARDWARE_CONFIG_TEXT', payload: config.rawHardwareConfigText });
        }
      } catch (error) {
        console.error('Error loading saved configuration:', error);
      }
    }
  }, [dispatch]);

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowLeft size={20} />}
            onClick={handleBack}
            sx={{ mb: 2 }}
          >
            Back to Welcome
          </Button>
          
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Configure Hardware
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            Set up your robot configuration and deck layout
          </Typography>
        </Box>

        <Paper elevation={2} sx={{ overflow: 'hidden' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Visual Configuration" />
              <Tab label="Text Configuration" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            {/* Visual Configuration */}
            <Grid container spacing={3} sx={{ p: 3 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Robot Model</InputLabel>
                  <Select
                    value={state.robotModel}
                    label="Robot Model"
                    onChange={(e) => handleRobotModelChange(e.target.value as RobotModel)}
                  >
                    {robotModels.map((model) => (
                      <MenuItem key={model} value={model}>{model}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>API Version</InputLabel>
                  <Select
                    value={state.apiVersion}
                    label="API Version"
                    onChange={(e) => handleApiVersionChange(e.target.value)}
                  >
                    {apiVersions.map((version) => (
                      <MenuItem key={version} value={version}>{version}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Left Pipette</InputLabel>
                  <Select
                    value={state.leftPipette || ''}
                    label="Left Pipette"
                    onChange={(e) => handleLeftPipetteChange(e.target.value as PipetteModel)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {pipetteOptions[state.robotModel].map((pipette) => (
                      <MenuItem key={pipette} value={pipette}>{pipette}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Right Pipette</InputLabel>
                  <Select
                    value={state.rightPipette || ''}
                    label="Right Pipette"
                    onChange={(e) => handleRightPipetteChange(e.target.value as PipetteModel)}
                  >
                    <MenuItem value="">None</MenuItem>
                    {pipetteOptions[state.robotModel].map((pipette) => (
                      <MenuItem key={pipette} value={pipette}>{pipette}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {state.robotModel === 'Flex' && (
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={state.useGripper}
                        onChange={(e) => handleGripperChange(e.target.checked)}
                      />
                    }
                    label="Use Gripper"
                  />
                </Grid>
              )}

              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Deck Layout
                </Typography>
                <Grid container spacing={2}>
                  {getDeckSlots(state.robotModel).map((slot) => (
                    <Grid item xs={6} sm={4} md={3} key={slot}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Slot {slot}</InputLabel>
                        <Select
                          value={state.deckLayout[slot]?.name || ''}
                          label={`Slot ${slot}`}
                          onChange={(e) => {
                            const selectedLabware = commonLabware.find(l => l.name === e.target.value);
                            handleLabwareChange(slot, selectedLabware || null);
                          }}
                        >
                          <MenuItem value="">Empty</MenuItem>
                          {commonLabware.map((labware) => (
                            <MenuItem key={labware.name} value={labware.name}>
                              {labware.displayName}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  ))}
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {/* Text Configuration */}
            <Box sx={{ p: 3 }}>
              <Alert severity="info" sx={{ mb: 3 }}>
                Enter your complete hardware configuration as text. This will override the visual configuration when saved.
              </Alert>
              
              <TextField
                fullWidth
                multiline
                rows={12}
                variant="outlined"
                label="Hardware Configuration"
                placeholder={`Robot Model: Flex
API Version: 2.20
Left Pipette: flex_1channel_1000
Right Pipette: None
Use Gripper: true
Deck Layout:
  A1: 1000μL Tip Rack
  B1: 96-well Plate
  C1: 12-well Reservoir`}
                value={rawConfigText}
                onChange={(e) => setRawConfigText(e.target.value)}
                sx={{ fontFamily: 'monospace' }}
              />
            </Box>
          </TabPanel>
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            variant="outlined"
            startIcon={<Save size={20} />}
            onClick={handleSaveConfiguration}
          >
            Save Configuration
          </Button>
          
          <Button
            variant="contained"
            endIcon={<ChevronRight size={20} />}
            onClick={handleNext}
            size="large"
          >
            Next: Define SOP
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default HardwareConfigPage;