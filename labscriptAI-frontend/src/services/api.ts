import axios from 'axios';
import { AppState, LabwareItem } from '../context/AppContext';

/**
 * API base URL resolution strategy:
 * 1. If VITE_API_BASE_URL is set → use it (user knows what they're doing)
 * 2. Else if DEV mode → fall back to http://127.0.0.1:8000
 * 3. Else (production) → empty string → same-origin /api requests via reverse proxy
 */
const normalizeBaseUrl = (value?: string): string => {
  const trimmed = value?.trim();
  return trimmed ? trimmed.replace(/\/+$/, '') : '';
};

const configuredApiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);

export const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl
  : import.meta.env.DEV
    ? 'http://127.0.0.1:8000'
    : '';
export const API_BASE_URL_LABEL = API_BASE_URL || 'same-origin (via reverse proxy)';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export interface SOPGenerationRequest {
  hardware_config: string;
  user_goal: string;
}

export interface ProtocolCodeGenerationRequest {
  sop_markdown: string;
  hardware_config: string;
  robot_model?: string; // Add explicit robot model field
}

export interface IterationLog {
  event_type: 'start' | 'initialization' | 'node_complete' | 'attempt_result' | 'final_result' | 'error' | 'stream_complete' | 'simulation_result' | 'feedback_prepared';
  message?: string;
  timestamp?: string;
  attempt_num?: number;
  
  // node_complete 相关字段
  node_name?: 'generator' | 'simulator' | 'feedback_preparer';
  has_code?: boolean;
  simulation_success?: boolean;
  has_warnings?: boolean;
  error_details?: string;
  error_analysis?: string;
  has_feedback?: boolean;
  
  // attempt_result 相关字段  
  status?: 'SUCCESS' | 'SUCCESS_WITH_WARNINGS' | 'FAILED' | 'FINAL_FAILED';
  final_code?: string;
  warning_details?: string;
  
  // final_result 相关字段
  generated_code?: string;
  total_attempts?: number;
  error_report?: string;
  
  // initialization 相关字段
  max_attempts?: number;
  
  // 其他可能的字段
  success?: boolean;
}

export interface CodeGenerationResult {
  success: boolean;
  generated_code: string;
  attempts: number;
  warnings: string[];
  iteration_logs: IterationLog[];
  timestamp: string;
}

export interface SimulationResult {
  success: boolean;
  raw_simulation_output: string;
  error_message?: string | null;
  warnings_present: boolean;
  warning_details?: string | null;
  final_status_message: string;
  timestamp: string;
}

export interface PyLabRobotProfile {
  robot_model: string;
  display_name: string;
  manufacturer: string;
  description: string;
  precision_class: string;
  volume_range: {
    min_ul: number;
    max_ul: number;
  };
  special_features: string[];
  recommended_for: string[];
  default_config: Record<string, any>; // Add this line
}

export interface PyLabRobotProfilesResponse {
  success: boolean;
  profiles: PyLabRobotProfile[];
  timestamp: string;
}

export const formatHardwareConfig = (state: AppState): string => {
    const deckItems = Object.entries(state.deckLayout)
      .filter(([, labware]: [string, LabwareItem | null]) => labware !== null)
      .map(([slot, labware]: [string, LabwareItem | null]) => `  ${slot}: ${labware?.name} (${labware?.displayName})`)
      .join('\n');
  
    return `Robot Model: ${state.robotModel}
API Version: ${state.apiVersion}
Left Pipette: ${state.leftPipette || 'None'}
Right Pipette: ${state.rightPipette || 'None'}
Use Gripper: ${state.useGripper}
Deck Layout:
${deckItems || '  (No labware configured)'}`;
};


export const apiService = {
    healthCheck: async () => {
        const response = await apiClient.get('/');
        return response.data;
    },

    generateSOPStream: async (
        params: SOPGenerationRequest,
        onToken: (token: string) => void,
        onComplete: () => void,
        onError: (error: string) => void
      ) => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/generate-sop-stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'text/event-stream',
            },
            body: JSON.stringify(params),
          });
      
          if (!response.ok || !response.body) {
            throw new Error(`Failed to get stream: ${response.statusText}`);
          }
      
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
      
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              onComplete();
              break;
            }
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');
      
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.substring(6);
                try {
                  const data = JSON.parse(dataStr);
                  if (data.token) {
                    onToken(data.token);
                  }
                } catch (e) {
                  console.error('Failed to parse stream data:', dataStr, e);
                }
              }
            }
          }
        } catch (error: unknown) {
          console.error('Stream error:', error);
          const message = error instanceof Error ? error.message : 'An unknown stream error occurred.';
          onError(message);
        }
    },
    
    generateProtocolCode: async (params: ProtocolCodeGenerationRequest): Promise<CodeGenerationResult> => {
        try {
            const response = await apiClient.post('/api/generate-protocol-code', params);
            return response.data;
        } catch (error: unknown) {
            console.error('Error generating protocol code:', error);
            if (axios.isAxiosError(error) && error.response && error.response.data && error.response.data.detail) {
                throw new Error(JSON.stringify(error.response.data.detail, null, 2));
            }
            throw error;
        }
    },

    converseSOP: async (params: { original_sop: string; user_instruction: string; hardware_context: string }): Promise<{ type: 'edit' | 'chat', content: string }> => {
        try {
          const response = await apiClient.post('/api/converse-sop', params);
          return response.data;
        } catch (error) {
          console.error('Error in SOP conversation:', error);
          throw error;
        }
    },

    converseCode: async (params: { original_code: string; user_instruction: string }): Promise<{ type: 'edit' | 'chat', content: string }> => {
        try {
          const response = await apiClient.post('/api/converse-code', params);
          return response.data;
        } catch (error) {
          console.error('Error in code conversation:', error);
          throw error;
        }
    },

    runSimulation: async (params: { python_code: string }): Promise<SimulationResult> => {
        try {
          const response = await apiClient.post('/api/simulate-protocol', params);
          return response.data;
        } catch (error) {
          console.error('Error running simulation:', error);
          throw error;
        }
    },

    runPyLabRobotSimulation: async (params: { protocol_code: string }): Promise<SimulationResult> => {
        try {
          const response = await apiClient.post('/api/simulate-pylabrobot-protocol', params);
          return response.data;
        } catch (error) {
          console.error('Error running PyLabRobot simulation:', error);
          throw error;
        }
    },

    getPyLabRobotProfiles: async (): Promise<PyLabRobotProfilesResponse> => {
        try {
            const response = await apiClient.get('/api/pylabrobot/profiles');
            return response.data;
        } catch (error) {
            console.error('Error fetching PyLabRobot profiles:', error);
            throw error;
        }
    },
};