# Runtime Freeze Questions

## 2026-05-22 EOPEN004 unified rerun provider failure

- Context: `runs/freeze_benchmark/unified/summary.json` had EOPEN004 as the only unified external-20 failure.
- Rerun: `runs/freeze_benchmark/unified_rerun_eopen004/summary.json`.
- Observed again: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`, `provider_error_count=1`, `package_complete_count=0`, `simulator_calls=0`, `total_tokens=0`.
- Initial classification: provider/API response parsing failure before package generation. It is not a validator or simulator failure.
- Follow-up diagnostics: added sidecar provider response logging and reran under `runs/freeze_benchmark/unified_rerun_eopen004_debug/`.
- Updated finding: at least one repeated `JSONDecodeError` came from a valid HTTP 200 JSON chat-completion response whose final assistant content was prose instead of the required JSON object. The benchmark records it as `provider_error_count=1`, but the plain-language cause is a model output contract violation, not a simulator or validator issue.
- Successful rerun: `runs/freeze_benchmark/unified_rerun_eopen004_debug/try05/summary.json` passed with `package_complete_count=1`, `validator_ok_count=1`, `simulation_pass_count=1`, and `first_pass_simulation_pass_count=1`.
