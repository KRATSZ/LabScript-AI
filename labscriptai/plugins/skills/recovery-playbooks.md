# Recovery playbooks (skill)



Live recovery path: `robot(op=status)` (embeds `parse_error` + `suggest_recovery` when `run_id` set) → operator/gate → `robot(op=act)` with recovery action or branch.



## Executable branches (`execute_protocol_recovery`)



1. **`retry_pick_up_tip_with_next_candidate`** — `TIP_PHYSICALLY_MISSING`; L0; same tiprack / next well **only when tip budget allows**.

2. **`substitute_liquid_source_with_attached_tip`** — `INSUFFICIENT_VOLUME` with same-liquid reserve and attached tip after probe-only `liquidNotFound`; L0 one-shot (see below).

3. **`suggest_new_destination_slot`** — `DESTINATION_OCCUPIED`; human-reviewed `destination_slot` required.

4. **`wait_and_poll_module_status`** — `MODULE_NOT_READY`; poll until ready then resume.

5. **`reconcile_state_first`** — module-blocker-only session diffs; reconcile before motion.



## Liquid source substitution (`INSUFFICIENT_VOLUME` + reserve + attached tip)



When `suggest_recovery.action` is **`substitute_liquid_source_with_attached_tip`**:



```

robot(op=act, action=recover_liquid_source_substitution, args={

  run_id, robot_ip, session_id,

  failed_source_key, preferred_source_key, protocol_path,

})

```



One step (like `recover_tip_pickup`): keep the **same run** in `awaiting-recovery`, enqueue **fixit** commands on the attached tip (probe reserve → transfer → drop), then stop the run after the suffix completes. Does **not** cancel the run first or start a new `run_protocol` with `pick_up_tip()`.



Equivalent: `execute_protocol_recovery` when guidance returns `substitute_liquid_source_with_attached_tip`.



**Volume gate.** A reserve that shares identity is not automatically enough. Check `volume_check` before substituting: `blocked_reason=substitute_volume_insufficient`, or `basis=declared_source_map` with `sufficient` false, means the reserve cannot cover the remaining transfers — refill or escalate, do not substitute. `basis=insufficient_data` means the required or usable volume is unknown, which is not the same as known-empty: stay on the human-confirmation path.

**Reserve LPD gate (in-run).** Before any substitute aspirate, fixit runs `liquidProbe` on the reserve. If that probe fails (`substitute_reserve_lpd_failed`), stop the experiment: drop the attached tip, stop the run, do not transfer. If the probe succeeds, estimate usable volume from liquid height via approximate labware geometry (`basis=approximate_lpd_height`, currently `nest_12_reservoir_15ml` prism + dead-volume ~1900 µL + 1.2 demand margin). When estimated usable volume is short, or height/geometry cannot be converted, stop with `substitute_reserve_volume_insufficient`. Only when the approximate gate passes does fixit continue aspirate/dispense. This estimate is coarse (V-bottom troughs overestimate low fills); it is a stop-gate, not precision metering.

**Destination plate height writeback (bookkeeping only).** For bench destination `nest_96_wellplate_200ul_flat`, `apply_liquid_probe_results` may convert `measure_height` / `height_mm` into `volume_ul` via approximate conical geometry and store `observed_height_mm` + `role=destination`. This is writeback only: it does not stop the run when the estimated destination volume looks low.



Without attached tip reuse: **manual_only** — refill primary or restart protocol.



Do **not** `resume_run` on the failed run when the uploaded protocol still targets the empty source. Do **not** stop the failed run and start a continuation protocol that calls `pick_up_tip()` while a tip is still attached.



## Manual-only (do not auto-act)



`INSUFFICIENT_VOLUME` without attached-tip reuse or reserve candidate, `AIR_BUBBLE`, `LIQUID_PROPERTY_ERROR`, `DECK_COLLISION`, `UNKNOWN_NEEDS_HUMAN`, dangerous `TIP_CLOG`, tip budget exhausted.



## Tip budget gate (before any tip recovery)



Stop — no `recover_tip_pickup`, `play`, or `resume_run` — when `tip_budget.enforced` is true and `tip_budget.sufficient` is false. Deck tips cannot cover the remaining `pick_up_tip` steps, so retrying only wastes the tips that are left.



`basis` records where the counts came from: `live_scan` (deck scan, the normal case), `protocol_metadata` (protocol also declares loaded wells), `none` (pickup count unknown). `none` means unadjudicated, not sufficient.



## Time window gate (before any resume)



When `time_window.expired` is true the assay validity is already lost: `abort` or `stop` only, never `play` or `resume_run`, even when the operator asks to continue. Offer discard/restart, or an explicit risk override that the operator must state.



`declared` false or `anchor_completed_at` missing means the window could not be adjudicated — treat it as unknown and ask the operator, not as satisfied.



## Contamination gate



A tip whose `contact_class` is `sample` must not aspirate or probe a well whose `role` is `common_stock`: drop it and pick up a fresh tip first. Read the role from `wells_summary[].role` or `well_roles`; the legacy `role` field in liquid tracking is a source filter, not a contamination role.



## Watch loop



Only L0 whitelist branches may auto-execute inside watch; `needs_user` / hard stop → BLOCKED.



## Act args (passthrough)



Common: `run_id`, `robot_ip`, `recovery_branch`, `session_id`, `failed_source_key`, `preferred_source_key`, `protocol_path`.



Or set `action` to `recover_liquid_source_substitution` or `recover_tip_pickup`.

