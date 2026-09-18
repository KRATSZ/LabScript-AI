import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
  useRef,
  ReactNode,
} from 'react';

// Types
export type RobotModel = 'Flex' | 'OT-2' | 'PyLabRobot';
export type PipetteModel = 
  | 'flex_1channel_1000' 
  | 'flex_1channel_50'
  | 'flex_8channel_1000' 
  | 'flex_8channel_50'
  | 'flex_96channel_1000'
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
  codeGenerationStatus: 'idle' | 'success' | 'warning' | 'error';
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

const APP_STATE_STORAGE_KEY = 'labscriptai.app-state.v1';
const APP_STATE_STORAGE_VERSION = 1;

interface PersistedAppState {
  version: number;
  state: AppState;
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
  | { type: 'SET_CODE_GENERATION_STATUS'; payload: AppState['codeGenerationStatus'] }
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
  apiVersion: '2.19',
  leftPipette: 'flex_1channel_1000',
  rightPipette: 'flex_8channel_1000',
  useGripper: true,
  deckLayout: {
    ...initialFlexDeck,
    'A1': { name: 'opentrons_flex_96_tiprack_1000ul', displayName: '1000 µL Flex Tips', type: 'tipRack' },
    'A3': { name: 'trash_bin', displayName: 'Flex Trash Bin', type: 'trash' },
    'B2': { name: 'corning_96_wellplate_360ul_flat', displayName: '96 Well 360 µL Plate', type: 'plate' },
    'C1': { name: 'nest_12_reservoir_15ml', displayName: '12-Well 15 mL Reservoir', type: 'reservoir' },
  },
  userGoal: '',
  generatedSop: '',
  pythonCode: '',
  codeGenerationStatus: 'idle',
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

const canUseStorage = (): boolean =>
  typeof window !== 'undefined' && window.localStorage != null;

const loadPersistedState = (): AppState => {
  if (!canUseStorage()) return initialState;

  try {
    const raw = window.localStorage.getItem(APP_STATE_STORAGE_KEY);
    if (raw == null) return initialState;

    const parsed = JSON.parse(raw) as Partial<PersistedAppState>;
    if (parsed.version !== APP_STATE_STORAGE_VERSION || parsed.state == null) {
      return initialState;
    }

    return {
      ...initialState,
      ...parsed.state,
      simulationResults: {
        ...initialState.simulationResults,
        ...parsed.state.simulationResults,
      },
      loading: false,
    };
  } catch (error) {
    console.warn('Failed to restore LabScript AI state:', error);
    return initialState;
  }
};

const persistState = (state: AppState): void => {
  if (!canUseStorage()) return;

  const payload: PersistedAppState = {
    version: APP_STATE_STORAGE_VERSION,
    state: {
      ...state,
      loading: false,
    },
  };

  try {
    window.localStorage.setItem(APP_STATE_STORAGE_KEY, JSON.stringify(payload));
  } catch (error) {
    console.warn('Failed to persist LabScript AI state:', error);
  }
};

const clearPersistedState = (): void => {
  if (!canUseStorage()) return;
  window.localStorage.removeItem(APP_STATE_STORAGE_KEY);
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
    case 'SET_CODE_GENERATION_STATUS':
      return { ...state, codeGenerationStatus: action.payload };
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
  const skipNextPersistRef = useRef(false);
  const [state, baseDispatch] = useReducer(
    appReducer,
    undefined,
    loadPersistedState
  );

  const dispatch = useCallback((action: AppAction): void => {
    if (action.type === 'RESET_STATE') {
      skipNextPersistRef.current = true;
      clearPersistedState();
    }
    baseDispatch(action);
  }, []);

  useEffect(() => {
    if (skipNextPersistRef.current) {
      skipNextPersistRef.current = false;
      clearPersistedState();
      return;
    }
    persistState(state);
  }, [state]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => useContext(AppContext);
