export type RobotModel = "OT-2" | "Flex" | "Hamilton" | "Tecan";

export type CheckStatus = "pass" | "fail" | "unevaluable";

export interface ChecksResult {
  status: CheckStatus;
  sim: { ok: boolean; reason?: string; errors?: string[] };
  logicpass: {
    outcome: string;
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
  consequences?: string[];
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
  plan: Record<string, unknown> | null;
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
}
