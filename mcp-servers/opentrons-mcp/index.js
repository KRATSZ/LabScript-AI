#!/usr/bin/env node

import fs from "fs";
import path from "path";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import {
  parseSimulationLog,
  runDoctorTool,
  runSimulationTool,
} from "./lib/simulation.js";

const DEFAULT_VERSION_HEADER = process.env.OPENTRONS_VERSION || "4";
const DEFAULT_PORT = process.env.OPENTRONS_PORT || "31950";

function asTextResponse(payload) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload, null, 2),
      },
    ],
  };
}

function normalizeBaseUrl(robotIp) {
  if (robotIp && /^https?:\/\//i.test(robotIp)) {
    return robotIp.replace(/\/$/, "");
  }
  if (robotIp) {
    return `http://${robotIp}:${DEFAULT_PORT}`;
  }
  if (process.env.OPENTRONS_HOST) {
    return process.env.OPENTRONS_HOST.replace(/\/$/, "");
  }
  throw new Error("robot_ip is required unless OPENTRONS_HOST is set.");
}

async function requestJson(method, url, { headers = {}, body = null } = {}) {
  const response = await fetch(url, {
    method,
    headers: {
      "Opentrons-Version": DEFAULT_VERSION_HEADER,
      ...headers,
    },
    body,
  });

  const contentType = response.headers.get("content-type") || "";
  const rawText = await response.text();
  const data = contentType.includes("application/json")
    ? JSON.parse(rawText || "null")
    : rawText;

  if (!response.ok) {
    throw new Error(
      JSON.stringify(
        {
          status: response.status,
          statusText: response.statusText,
          error: data,
        },
        null,
        2,
      ),
    );
  }

  return data;
}

async function uploadProtocol(args) {
  const { robot_ip, file_path, protocol_kind, key, run_time_parameters } = args;
  const protocolPath = path.resolve(file_path);
  if (!fs.existsSync(protocolPath)) {
    throw new Error(`Protocol file not found: ${protocolPath}`);
  }

  const form = new FormData();
  const fileBuffer = fs.readFileSync(protocolPath);
  form.append(
    "files",
    new Blob([fileBuffer], { type: "text/x-python" }),
    path.basename(protocolPath),
  );
  if (protocol_kind) {
    form.append("protocolKind", protocol_kind);
  }
  if (key) {
    form.append("key", key);
  }
  if (run_time_parameters) {
    form.append("runTimeParameterValues", JSON.stringify(run_time_parameters));
  }

  const baseUrl = normalizeBaseUrl(robot_ip);
  return requestJson("POST", `${baseUrl}/protocols`, { body: form });
}

async function getRunStatus(args) {
  const baseUrl = normalizeBaseUrl(args.robot_ip);
  const [run, commands] = await Promise.all([
    requestJson("GET", `${baseUrl}/runs/${args.run_id}`),
    requestJson("GET", `${baseUrl}/runs/${args.run_id}/commands?pageLength=10`),
  ]);
  return {
    run,
    commands,
  };
}

class OpentronsLabMCP {
  constructor() {
    this.server = new Server(
      {
        name: "opentrons-lab-mcp",
        version: "0.1.0",
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    this.setupTools();
  }

  setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "robot_health",
          description: "Check robot connectivity and health via /health.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
            },
          },
        },
        {
          name: "get_protocols",
          description: "List protocols stored on the robot.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
            },
          },
        },
        {
          name: "upload_protocol",
          description: "Upload a local protocol file to the robot.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
              file_path: { type: "string", description: "Path to protocol file" },
              protocol_kind: {
                type: "string",
                enum: ["standard", "quick-transfer"],
              },
              key: { type: "string" },
              run_time_parameters: { type: "object" },
            },
            required: ["file_path"],
          },
        },
        {
          name: "create_run",
          description: "Create a run for a protocol already on the robot.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
              protocol_id: { type: "string", description: "Uploaded protocol ID" },
              run_time_parameters: { type: "object" },
            },
            required: ["protocol_id"],
          },
        },
        {
          name: "control_run",
          description: "Play, pause, stop, or resume-from-recovery for a run.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
              run_id: { type: "string" },
              action: {
                type: "string",
                enum: ["play", "pause", "stop", "resume-from-recovery"],
              },
            },
            required: ["run_id", "action"],
          },
        },
        {
          name: "get_runs",
          description: "List runs on the robot.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
            },
          },
        },
        {
          name: "get_run_status",
          description: "Get a run plus its recent command history.",
          inputSchema: {
            type: "object",
            properties: {
              robot_ip: { type: "string", description: "Robot IP or full base URL" },
              run_id: { type: "string" },
            },
            required: ["run_id"],
          },
        },
        {
          name: "doctor_local_runtime",
          description: "Probe whether the local Python environment can import opentrons.simulate.",
          inputSchema: {
            type: "object",
            properties: {
              workspace_root: { type: "string" },
              api_root: { type: "string" },
              shared_data_root: { type: "string" },
              python_executable: { type: "string" },
            },
          },
        },
        {
          name: "simulate_protocol",
          description: "Run local opentrons.simulate against a protocol file and return structured logs.",
          inputSchema: {
            type: "object",
            properties: {
              protocol_path: { type: "string" },
              workspace_root: { type: "string" },
              api_root: { type: "string" },
              shared_data_root: { type: "string" },
              python_executable: { type: "string" },
              extra_args: {
                type: "array",
                items: { type: "string" },
              },
              max_log_chars: { type: "integer", default: 20000 },
            },
            required: ["protocol_path"],
          },
        },
        {
          name: "parse_simulation_output",
          description: "Classify simulation stdout/stderr into structured repair categories.",
          inputSchema: {
            type: "object",
            properties: {
              simulation_output_json: { type: "string" },
              stdout: { type: "string" },
              stderr: { type: "string" },
              exit_code: { type: "integer" },
              protocol_path: { type: "string" },
            },
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async request => {
      const { name, arguments: args = {} } = request.params;

      try {
        switch (name) {
          case "robot_health":
            return asTextResponse(
              await requestJson("GET", `${normalizeBaseUrl(args.robot_ip)}/health`),
            );
          case "get_protocols":
            return asTextResponse(
              await requestJson("GET", `${normalizeBaseUrl(args.robot_ip)}/protocols`),
            );
          case "upload_protocol":
            return asTextResponse(await uploadProtocol(args));
          case "create_run":
            return asTextResponse(
              await requestJson("POST", `${normalizeBaseUrl(args.robot_ip)}/runs`, {
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  data: {
                    protocolId: args.protocol_id,
                    ...(args.run_time_parameters
                      ? { runTimeParameterValues: args.run_time_parameters }
                      : {}),
                  },
                }),
              }),
            );
          case "control_run":
            return asTextResponse(
              await requestJson(
                "POST",
                `${normalizeBaseUrl(args.robot_ip)}/runs/${args.run_id}/actions`,
                {
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    data: {
                      actionType: args.action,
                    },
                  }),
                },
              ),
            );
          case "get_runs":
            return asTextResponse(
              await requestJson("GET", `${normalizeBaseUrl(args.robot_ip)}/runs`),
            );
          case "get_run_status":
            return asTextResponse(await getRunStatus(args));
          case "doctor_local_runtime":
            return asTextResponse(await runDoctorTool(args));
          case "simulate_protocol":
            return asTextResponse(await runSimulationTool(args));
          case "parse_simulation_output":
            return asTextResponse(parseSimulationLog(args));
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return asTextResponse({
          success: false,
          tool: name,
          error: error.message,
        });
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Opentrons Lab MCP server running on stdio");
  }
}

const server = new OpentronsLabMCP();
server.run().catch(error => {
  console.error(error);
  process.exit(1);
});
