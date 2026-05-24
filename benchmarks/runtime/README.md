# Runtime20 Benchmark

`runtime20.yaml` is the frozen runtime recovery benchmark for real-machine or
machine-equivalent liquid-handler execution checks.

Freeze rule: do not edit the 20 case definitions after 2026-05-21. Future work
should add run results, traces, videos, and hardware-availability notes without
changing the cases.

Claim boundary:

- This is separate from the 90-task authoring benchmark.
- This is separate from the external 66-task generalization benchmark.
- A case can be run on a physical robot, in a read-only/shadow setting, or not
  run because hardware is unavailable, but the case itself must remain fixed.

The cases intentionally favor common liquid-handler failures: consumables,
deck/labware state, liquid state, module/gripper state, and human-confirmed
resume. Opentrons documentation supplies concrete examples, while PyLabRobot,
Autoprotocol, and SiLA-style sources support the platform-neutral wording.
