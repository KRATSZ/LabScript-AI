# Diff Workflow Ablation

This guide documents the changes that permanently disable the diff-based token saving workflow so the project runs in a full-rewrite mode.

## Switches Introduced
- `backend/langchain_agent.py` always requests complete outputs from the LLM:
  - `generate_code_node` regenerates the entire Opentrons script on every attempt, using prior feedback only as context.
  - `modify_code_tool` rewrites the entire script in response to edit instructions.
  - `_edit_sop_with_diff` (name preserved for compatibility) rebuilds the whole Markdown document instead of applying SEARCH/REPLACE patches.

## Running The Ablation
1. Trigger the usual protocol-generation or code-editing flows (e.g. call `/api/generate-protocol-code`, use the code conversation endpoints, or run the frontend workflow). The system will now send full documents/code to the LLM for every iteration.
2. Capture latency and token-consumption metrics from your monitoring stack or OpenAI dashboard to compare against the historical diff-enabled baseline.

## Reverting
- Revert the Git changes to restore the original diff-based behaviour.
