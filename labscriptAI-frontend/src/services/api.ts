// API service layer for LabScript AI frontend
import { AppState } from '../context/AppContext';

// API base URL - can be configured via environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Types for API requests and responses
export interface SOPGenerationRequest {
  hardware_config: string;
  user_goal: string;
}

export interface SOPGenerationResponse {
  success: boolean;
  sop_markdown: string;
  timestamp: string;
}

export interface ProtocolCodeGenerationRequest {
  sop_markdown: string;
  hardware_config: string;
}

export interface ProtocolSimulationRequest {
  protocol_code: string;
}

export interface ProtocolSimulationResponse {
  success: boolean;
  raw_simulation_output: string;
  error_message?: string | null;
  warnings_present: boolean;
  warning_details?: string | null;
  final_status_message: string;
  timestamp: string;
}

// Helper function to format hardware config for API
export const formatHardwareConfig = (state: AppState): string => {
  const deckItems = Object.entries(state.deckLayout)
    .filter(([_, labware]) => labware !== null)
    .map(([slot, labware]) => `  ${slot}: ${labware?.displayName}`)
    .join('\n');

  return `Robot Model: ${state.robotModel}
API Version: ${state.apiVersion}
Left Pipette: ${state.leftPipette || 'None'}
Right Pipette: ${state.rightPipette || 'None'}
Use Gripper: ${state.useGripper}
Deck Layout:
${deckItems || '  (No labware configured)'}`;
};

// API service class
export class ApiService {
  private static instance: ApiService;
  
  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error(`API server is not available: ${error}`);
    }
  }

  // Generate SOP
  async generateSOP(request: SOPGenerationRequest): Promise<SOPGenerationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-sop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(`SOP generation failed: ${errorData.message || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('SOP generation error:', error);
      throw error;
    }
  }

  // Generate protocol code with simple HTTP request (no SSE)
  async generateProtocolCode(
    request: ProtocolCodeGenerationRequest,
    onProgress?: (message: string) => void
  ): Promise<{
    success: boolean;
    generated_code: string;
    attempts: number;
    warnings: string[];
    iteration_logs: Array<Record<string, any>>;
    timestamp: string;
  }> {
    console.log("[ApiService] Attempting to generate protocol code with request:", JSON.stringify(request, null, 2));
    try {
      if (onProgress) onProgress('Sending code generation request...');
      console.log("[ApiService] Fetching from:", `${API_BASE_URL}/api/generate-protocol-code`);

      const response = await fetch(`${API_BASE_URL}/api/generate-protocol-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      console.log("[ApiService] Received response status:", response.status);

      if (!response.ok) {
        let errorMessage = `Code generation API request failed with status ${response.status}`;
        try {
            const errorData = await response.json();
            console.error("[ApiService] Code generation failed. Server responded with error data:", errorData);
            if (errorData.detail && typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail.details && typeof errorData.detail.details === 'string'){
              errorMessage = errorData.detail.details;
            } else if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail.error && typeof errorData.detail.error === 'string') {
              errorMessage = `${errorData.detail.error}: ${errorData.detail.message || 'No additional message.'}`;
            } else if (errorData.message && typeof errorData.message === 'string') {
              errorMessage = errorData.message;
            } else if (typeof errorData.detail === 'object') {
                errorMessage = `Server error: ${JSON.stringify(errorData.detail)}`;
            }
        } catch (jsonError) {
            console.error("[ApiService] Code generation failed. Server response was not valid JSON. Status Text:", response.statusText);
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log("[ApiService] Successfully received and parsed result:", JSON.stringify(result, null, 2));
      
      if (onProgress) {
        if (result.warnings && result.warnings.length > 0) {
          onProgress(`Code generation completed (${result.attempts} attempts) with ${result.warnings.length} warnings`);
        } else {
          onProgress(`Code generation successful (${result.attempts} attempts)`);
        }
      }

      return result;
    } catch (error: any) {
      console.error('[ApiService] Critical error in generateProtocolCode:', error);
      console.error("[ApiService] Error name:", error.name, "Message:", error.message, "Stack:", error.stack);
      if (onProgress) onProgress(`Code generation request failed: ${error.message}`);
      throw error;
    }
  }

  // Simulate protocol
  async simulateProtocol(request: ProtocolSimulationRequest): Promise<ProtocolSimulationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/simulate-protocol`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(`Protocol simulation failed: ${errorData.message || response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Protocol simulation error:', error);
      throw error;
    }
  }

  // Get available tools
  async getTools(): Promise<{ tools: Array<{ name: string; description: string }> }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools`);
      if (!response.ok) {
        throw new Error(`Failed to get tools: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Get tools error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const apiService = ApiService.getInstance();