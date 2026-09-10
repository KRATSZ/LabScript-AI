export type RobotModel = "OT-2" | "Flex";

export interface ChecksResult {
  sim: { ok: boolean; reason?: string; errors?: string[] };
  logicpass: {
    outcome: string;
    logic_pass: boolean;
    final_pass_v2?: boolean;
    issues?: unknown[];
    coverage?: unknown;
    reason?: string;
  };
  statepass: {
    issues?: unknown[];
    coverage?: unknown;
    reason?: string;
    [key: string]: unknown;
  };
  llmreview?: {
    match?: boolean;
    findings?: unknown[];
    reason?: string;
  };
  fab: { lit: boolean };
}

export interface SessionSnapshot {
  id: string;
  phase: string;
  missing: string[];
  goal: string;
  doc: string;
  robot: RobotModel | null;
  hardware: {
    leftPipette?: string;
    rightPipette?: string;
    useGripper?: boolean;
    apiVersion?: string;
    deck: Record<string, string>;
  };
  hardware_config: string;
  sop: string;
  code: string;
  analyze: Record<string, unknown> | null;
  checks: ChecksResult | null;
  fab: { lit: boolean };
  deck_assumed?: boolean;
  code_service?: "up" | "down";
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  meta?: string;
  thinking?: string;
  tools?: string[];
}
