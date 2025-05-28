import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// Types
export type RobotModel = 'Flex' | 'OT-2' | 'PyLabRobot';
export type PipetteModel = 
  | 'flex_1channel_1000' 
  | 'flex_1channel_300' 
  | 'flex_8channel_1000' 
  | 'flex_8channel_300'
  | 'p1000_single_gen2' 
  | 'p300_single_gen2' 
  | 'p20_single_gen2'
  | 'p1000_multi_gen2' 
  | 'p300_multi_gen2' 
  | 'p20_multi_gen2'
  | 'pylabrobot_1000'
  | 'pylabrobot_300'
  | 'pylabrobot_50'
  | null;

export interface LabwareItem {
  type: string;
  name: string;
  displayName: string;
}

export interface AppState {
  robotModel: RobotModel;
  apiVersion: string;
  leftPipette: PipetteModel;
  rightPipette: PipetteModel;
  useGripper: boolean;
  deckLayout: Record<string, LabwareItem | null>;
  userGoal: string;
  generatedSop: string;
  pythonCode: string;
  rawHardwareConfigText?: string | null;
  simulationResults: {
    status: 'idle' | 'success' | 'warning' | 'error';
    message: string;
    details: string;
    suggestions: string[];
    raw_simulation_output?: string | null;
    warnings_present?: boolean;
  };
  loading: boolean;
}

// Action types
type AppAction =
  | { type: 'SET_ROBOT_MODEL'; payload: RobotModel }
  | { type: 'SET_API_VERSION'; payload: string }
  | { type: 'SET_LEFT_PIPETTE'; payload: PipetteModel }
  | { type: 'SET_RIGHT_PIPETTE'; payload: PipetteModel }
  | { type: 'SET_USE_GRIPPER'; payload: boolean }
  | { type: 'SET_DECK_LABWARE'; payload: { slot: string; labware: LabwareItem | null } }
  | { type: 'SET_USER_GOAL'; payload: string }
  | { type: 'SET_GENERATED_SOP'; payload: string }
  | { type: 'SET_PYTHON_CODE'; payload: string }
  | { type: 'SET_RAW_HARDWARE_CONFIG_TEXT'; payload: string | null }
  | { type: 'SET_SIMULATION_RESULTS'; payload: AppState['simulationResults'] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'RESET_STATE' };

// Initial state
const initialFlexDeck: Record<string, LabwareItem | null> = {
  'A1': null, 'A2': null, 'A3': null,
  'B1': null, 'B2': null, 'B3': null,
  'C1': null, 'C2': null, 'C3': null,
  'D1': null, 'D2': null, 'D3': null,
};

const initialOT2Deck: Record<string, LabwareItem | null> = {
  '1': null, '2': null, '3': null,
  '4': null, '5': null, '6': null,
  '7': null, '8': null, '9': null,
  '10': null, '11': null,
};

const initialPyLabRobotDeck: Record<string, LabwareItem | null> = {
  'P1': null, 'P2': null, 'P3': null, 'P4': null,
  'P5': null, 'P6': null, 'P7': null, 'P8': null,
  'P9': null, 'P10': null, 'P11': null, 'P12': null,
};

const initialState: AppState = {
  robotModel: 'Flex',
  apiVersion: '2.20',
  leftPipette: null,
  rightPipette: null,
  useGripper: false,
  deckLayout: initialFlexDeck,
  userGoal: '',
  generatedSop: '',
  pythonCode: '',
  rawHardwareConfigText: null,
  simulationResults: {
    status: 'idle',
    message: '',
    details: '',
    suggestions: [],
    raw_simulation_output: null,
    warnings_present: false,
  },
  loading: false,
};

// Reducer
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_ROBOT_MODEL':
      return {
        ...state,
        robotModel: action.payload,
        // Reset deck layout based on robot model
        deckLayout: action.payload === 'Flex' 
          ? initialFlexDeck 
          : action.payload === 'OT-2'
          ? initialOT2Deck
          : initialPyLabRobotDeck,
        // Reset pipettes and gripper as they're model-specific
        leftPipette: null,
        rightPipette: null,
        useGripper: false,
      };
    case 'SET_API_VERSION':
      return { ...state, apiVersion: action.payload };
    case 'SET_LEFT_PIPETTE':
      return { ...state, leftPipette: action.payload };
    case 'SET_RIGHT_PIPETTE':
      return { ...state, rightPipette: action.payload };
    case 'SET_USE_GRIPPER':
      return { ...state, useGripper: action.payload };
    case 'SET_DECK_LABWARE':
      return {
        ...state,
        deckLayout: {
          ...state.deckLayout,
          [action.payload.slot]: action.payload.labware,
        },
      };
    case 'SET_USER_GOAL':
      return { ...state, userGoal: action.payload };
    case 'SET_GENERATED_SOP':
      return { ...state, generatedSop: action.payload };
    case 'SET_PYTHON_CODE':
      return { ...state, pythonCode: action.payload };
    case 'SET_RAW_HARDWARE_CONFIG_TEXT':
      return { ...state, rawHardwareConfigText: action.payload };
    case 'SET_SIMULATION_RESULTS':
      return { ...state, simulationResults: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'RESET_STATE':
      return initialState;
    default:
      return state;
  }
};

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}>({
  state: initialState,
  dispatch: () => null,
});

// Provider component
export const AppContextProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => useContext(AppContext);