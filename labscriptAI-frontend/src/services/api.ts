import axios from 'axios';
import { AppState, LabwareItem } from '../context/AppContext';
import type { ProtocolAnalysisOutput } from '../../../web/opentrons-protocol-visualizer-web-slim/shared-data/js';

const normalizeBaseUrl = (value?: string): string => {
  const trimmed = value?.trim();
  return trimmed ? trimmed.replace(/\/+$/, '') : '';
};

const DEFAULT_LOCAL_API_BASE_URL = 'http://127.0.0.1:8000';

export const API_BASE_URL =
  normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL) || DEFAULT_LOCAL_API_BASE_URL;
export const API_BASE_URL_LABEL = API_BASE_URL || 'same-origin';

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

export type VisualizerAnalyzeProgressPhase =
  | 'submitting'
  | 'submitted'
  | 'queued'
  | 'running';

export interface VisualizerAnalyzeOptions {
  check?: boolean;
  onProgress?: (phase: VisualizerAnalyzeProgressPhase) => void;
}

// protocols.io 导出请求接口
export interface ProtocolExportRequest {
  user_goal: string;
  hardware_config: string;
  sop_markdown: string;
  generated_code: string;
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

const VISUALIZER_ANALYZE_PREFIX = '/api/visualizer/analyze';
const VISUALIZER_ANALYZE_POLL_MS = 900;
const VISUALIZER_ANALYZE_MAX_WAIT_MS = 15 * 60 * 1000;

const buildVisualizerAnalyzeFormData = (
  protocol: File,
  options: VisualizerAnalyzeOptions = {}
): FormData => {
  const fd = new FormData();
  fd.append('protocol', protocol);
  if (options.check === true) {
    fd.append('check', 'true');
  }
  return fd;
};

const sleep = (ms: number): Promise<void> =>
  new Promise(resolve => window.setTimeout(resolve, ms));

const formatDetail = (detail: unknown): string => {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((entry: { msg?: string }) => entry?.msg ?? JSON.stringify(entry))
      .join('; ');
  }
  return JSON.stringify(detail);
};

interface VisualizerJobStatusBody {
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: ProtocolAnalysisOutput;
  error?: string;
}

export const analyzeProtocolForVisualization = async (
  protocol: File,
  options: VisualizerAnalyzeOptions = {}
): Promise<ProtocolAnalysisOutput> => {
  const { onProgress, ...rest } = options;
  let lastPhase: VisualizerAnalyzeProgressPhase | null = null;
  const emit = (phase: VisualizerAnalyzeProgressPhase): void => {
    if (phase !== lastPhase) {
      lastPhase = phase;
      onProgress?.(phase);
    }
  };

  emit('submitting');
  const startRes = await fetch(`${API_BASE_URL}${VISUALIZER_ANALYZE_PREFIX}/start`, {
    method: 'POST',
    body: buildVisualizerAnalyzeFormData(protocol, rest),
  });

  if (!startRes.ok) {
    let message = startRes.statusText;
    try {
      const body = (await startRes.json()) as { detail?: unknown };
      if (body.detail != null) message = formatDetail(body.detail);
    } catch {
      // ignore
    }
    throw new Error(message);
  }

  const { job_id: jobId } = (await startRes.json()) as { job_id: string };
  emit('submitted');

  const deadline = Date.now() + VISUALIZER_ANALYZE_MAX_WAIT_MS;
  while (Date.now() < deadline) {
    await sleep(VISUALIZER_ANALYZE_POLL_MS);
    const response = await fetch(
      `${API_BASE_URL}${VISUALIZER_ANALYZE_PREFIX}/jobs/${jobId}`
    );

    if (!response.ok) {
      let message = response.statusText;
      try {
        const body = (await response.json()) as { detail?: unknown };
        if (body.detail != null) message = formatDetail(body.detail);
      } catch {
        // ignore
      }
      throw new Error(message);
    }

    const body = (await response.json()) as VisualizerJobStatusBody;
    if (body.status === 'pending') {
      emit('queued');
    } else if (body.status === 'running') {
      emit('running');
    }

    if (body.status === 'completed') {
      if (body.result == null) {
        throw new Error('Analysis completed but result was missing');
      }
      return body.result;
    }

    if (body.status === 'failed') {
      throw new Error(body.error ?? 'Analysis failed');
    }
  }

  throw new Error('Protocol analysis timed out while waiting for the server job');
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

    // 导出协议到 protocols.io 格式的 zip 文件
    exportForProtocolsIO: async (params: ProtocolExportRequest): Promise<Blob> => {
        try {
            const response = await apiClient.post('/api/export/protocols-io', params, {
                responseType: 'blob', // 重要：指定响应类型为 blob
            });
            return response.data;
        } catch (error) {
            console.error('Error exporting for protocols.io:', error);
            throw error;
        }
    },
};
