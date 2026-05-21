from __future__ import annotations

import unittest

from labscriptai.ir import (
    LabFlowIR,
    compile_to_opentrons_protocol,
    export_pylabrobot_actions,
    validate_labflow_ir,
)


def minimal_transfer_ir() -> dict:
    return {
        "schema_version": "0.1",
        "protocol_id": "X001",
        "description": "Copy A1 into B1.",
        "resources": [
            {
                "id": "tips",
                "type": "tiprack",
                "backend_name": "opentrons_flex_96_tiprack_200ul",
                "slot": "1",
            },
            {
                "id": "plate",
                "type": "plate",
                "backend_name": "corning_96_wellplate_360ul_flat",
                "slot": "2",
            },
            {
                "id": "p300",
                "type": "pipette",
                "backend_name": "flex_1channel_1000",
                "mount": "left",
                "metadata": {"tipracks": ["tips"]},
            },
        ],
        "operations": [
            {
                "id": "op1",
                "op": "transfer",
                "source": "plate:A1",
                "destination": "plate:B1",
                "volume_ul": 25,
                "reagent": "sample",
                "constraints": {"tip_policy": "new_tip", "avoid_contamination": True},
            }
        ],
    }


class LabFlowIRTests(unittest.TestCase):
    def test_validate_and_export_pylabrobot_style_actions(self) -> None:
        ir = LabFlowIR.from_dict(minimal_transfer_ir())

        ok, reasons = validate_labflow_ir(ir)
        actions = export_pylabrobot_actions(ir)

        self.assertTrue(ok, reasons)
        self.assertEqual(
            [action["action"] for action in actions],
            ["pick_up_tip", "aspirate", "dispense", "drop_tip"],
        )
        self.assertEqual(actions[1]["source"], "plate:A1")
        self.assertEqual(actions[2]["destination"], "plate:B1")

    def test_compile_to_opentrons_protocol_skeleton(self) -> None:
        protocol = compile_to_opentrons_protocol(minimal_transfer_ir())

        self.assertIn("protocol.load_labware('corning_96_wellplate_360ul_flat', '2')", protocol)
        self.assertIn("protocol.load_instrument('flex_1channel_1000', 'left'", protocol)
        self.assertIn("p300.transfer(25.0", protocol)
        self.assertIn("plate['A1']", protocol)
        self.assertIn("plate['B1']", protocol)

    def test_invalid_ir_reports_human_readable_reasons(self) -> None:
        payload = minimal_transfer_ir()
        payload["operations"][0]["destination"] = "unknown:B1"

        ok, reasons = validate_labflow_ir(payload)

        self.assertFalse(ok)
        self.assertIn("op1: destination resource is unknown: unknown", reasons)

    def test_common_model_aliases_are_normalized(self) -> None:
        payload = minimal_transfer_ir()
        payload["resources"][1]["type"] = "96_well_plate"
        payload["operations"][0].pop("op")
        payload["operations"][0]["type"] = "transfer"
        payload["operations"][0].pop("volume_ul")
        payload["operations"][0]["volume"] = 25

        ir = LabFlowIR.from_dict(payload)
        ok, reasons = validate_labflow_ir(ir)

        self.assertTrue(ok, reasons)
        self.assertEqual(ir.resources[1].type, "plate")
        self.assertEqual(ir.operations[0].op, "transfer")
        self.assertEqual(ir.operations[0].volume_ul, 25.0)

    def test_mix_exports_single_action(self) -> None:
        payload = minimal_transfer_ir()
        payload["protocol_id"] = "X002"
        payload["operations"] = [
            {
                "id": "mix1",
                "op": "mix",
                "source": "plate:A1",
                "volume_ul": 30,
                "repetitions": 5,
            }
        ]

        actions = export_pylabrobot_actions(payload)

        self.assertEqual(actions, [{"action": "mix", "operation_id": "mix1", "location": "plate:A1", "volume_ul": 30.0, "repetitions": 5}])

    def test_nested_model_steps_and_slash_locations_are_normalized(self) -> None:
        payload = {
            "schema_version": "1.0",
            "protocol_id": "X003",
            "resources": [
                {"id": "p1", "type": "pipette"},
                {"id": "tips", "type": "tip_rack"},
                {"id": "res1", "type": "reservoir"},
                {"id": "plt1", "type": "96_well_plate"},
            ],
            "operations": [
                {
                    "id": "transfer",
                    "type": "transfer",
                    "steps": [
                        {"type": "aspirate", "source": "res1/A1", "volume": 20},
                        {"type": "dispense", "destination": "plt1/A1", "volume": 20},
                    ],
                },
                {"id": "mix_a1", "type": "mix", "location": "plt1/A1", "volume": 10, "repetitions": 3},
            ],
        }

        ir = LabFlowIR.from_dict(payload)
        ok, reasons = validate_labflow_ir(ir)
        actions = export_pylabrobot_actions(ir)

        self.assertTrue(ok, reasons)
        self.assertEqual(ir.schema_version, "0.1")
        self.assertEqual([operation.op for operation in ir.operations], ["aspirate", "dispense", "mix"])
        self.assertEqual(ir.operations[0].source, "res1:A1")
        self.assertEqual(ir.operations[1].destination, "plt1:A1")
        self.assertEqual(ir.operations[2].source, "plt1:A1")
        self.assertEqual([action["action"] for action in actions], ["aspirate", "dispense", "mix"])

    def test_model_resource_mapping_and_dest_alias_are_normalized(self) -> None:
        payload = {
            "schema_version": 1,
            "protocol_id": "X004",
            "resources": {
                "pipette": {"type": "p300_single_gen2", "mount": "left"},
                "tiprack": {"type": "opentrons_96_tiprack_300ul", "slot": "1"},
                "reservoir": {"type": "nest_12_reservoir_15ml", "slot": "2"},
                "plate": {"type": "corning_96_wellplate_360ul_flat", "slot": "3"},
            },
            "operations": [
                {"op": "transfer", "source": "reservoir:A1", "dest": "plate:A1", "volume_ul": 20},
                {"op": "mix", "location": "plate:A1", "volume_ul": 10, "repetitions": 3},
            ],
        }

        ir = LabFlowIR.from_dict(payload)
        ok, reasons = validate_labflow_ir(ir)
        protocol = compile_to_opentrons_protocol(ir)

        self.assertTrue(ok, reasons)
        self.assertEqual([(resource.id, resource.type) for resource in ir.resources], [
            ("pipette", "pipette"),
            ("tiprack", "tiprack"),
            ("reservoir", "reservoir"),
            ("plate", "plate"),
        ])
        self.assertIn("protocol.load_instrument('p300_single_gen2', 'left'", protocol)
        self.assertIn("pipette.transfer(20.0, reservoir['A1'], plate['A1']", protocol)


if __name__ == "__main__":
    unittest.main()
