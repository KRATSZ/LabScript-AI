export type RobotModel = "OT-2" | "Flex" | "Hamilton" | "Vantage" | "Tecan";
export type CodegenKind = "opentrons_python" | "plan_ir";

export interface DeviceCard {
  id: string;
  label: string;
  legacyRobot: RobotModel;
  codegen: CodegenKind;
  animation: boolean;
  blurb: string;
}

export type UiLang = "en" | "zh";

export interface StartInput {
  goal: string;
  doc: string;
  robot: RobotModel;
  language?: UiLang;
}

export type CheckStatus = "pass" | "fail" | "unevaluable";

export type AgentEventKind =
  | "turn/start"
  | "turn/end"
  | "step/start"
  | "step/end"
  | "tool/call"
  | "tool/result";

export interface AgentEvent {
  seq: number;
  t: number;
  kind: AgentEventKind;
  name?: string;
  detail?: Record<string, unknown>;
}

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
  compile?: {
    ok: boolean;
    stage?: string;
    error?: string;
    hint?: string;
    warnings?: string[];
    command_count?: number;
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
  artifacts?: {
    worklistGwl?: string;
    scriptXml?: string;
    hamiltonScript?: string;
  } | null;
  checks: ChecksResult | null;
  fab: { lit: boolean };
  deck_assumed?: boolean;
  code_service?: "up" | "down";
  events?: AgentEvent[];
  device_id?: string | null;
  device_label?: string | null;
  device_note?: string | null;
  intake_done?: boolean;
  language?: UiLang;
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  meta?: string;
  thinking?: string;
}
