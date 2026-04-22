from __future__ import annotations

import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
VISION_SCRIPT = ROOT / "mcp-servers" / "opentrons-mcp" / "scripts" / "vision_check.py"
SIDECAR_SCRIPT = ROOT.parent / "labagentyolo" / "scripts" / "export_deck_sidecars_from_labelme.py"

VISION = runpy.run_path(str(VISION_SCRIPT))
SIDECAR = runpy.run_path(str(SIDECAR_SCRIPT))

_build_slot_coverage = VISION["_build_slot_coverage"]
_build_slot_observations = VISION["_build_slot_observations"]
_compute_mismatches = VISION["_compute_mismatches"]
_apply_mismatch_flags = VISION["_apply_mismatch_flags"]
_pick_ordered_deck_corners = VISION["_pick_ordered_deck_corners"]
_select_covered_slots = VISION["_select_covered_slots"]
extract_deck_quad_norm = SIDECAR["extract_deck_quad_norm"]


class VisionCheckLogicTests(unittest.TestCase):
    def test_build_slot_coverage_can_span_multiple_slots(self) -> None:
        coverage = _build_slot_coverage(0.0, 0.0, 90.0, 255.0, 300, 300, None, label="module")

        self.assertEqual(coverage["covered_slots"], ["A1", "B1", "C1"])
        self.assertIn("coverage_spans_multiple_slots", coverage["coverage_notes"])
        self.assertIn("uniform_grid_fallback", coverage["coverage_notes"])

    def test_tiprack_policy_does_not_spill_into_neighbor_slot(self) -> None:
        covered = _select_covered_slots(
            {"C2": 0.055, "C3": 0.0335},
            primary_slot="C2",
            poly_area=0.0885,
            polygon=[[0.4394, 0.4673], [0.8074, 0.4115], [0.8045, 0.7375], [0.4506, 0.7557]],
            label="tiprack",
        )

        self.assertEqual(covered, ["C2"])

    def test_module_policy_keeps_vertical_spill_but_blocks_weaker_horizontal_spill(self) -> None:
        vertical = _select_covered_slots(
            {"C1": 0.0772, "B1": 0.0430},
            primary_slot="C1",
            poly_area=0.1202,
            polygon=[[0.0134, 0.3019], [0.4057, 0.4533], [0.3796, 0.8793], [0.0291, 0.7634]],
            label="module",
        )
        horizontal = _select_covered_slots(
            {"C3": 0.0636, "B3": 0.0303},
            primary_slot="C3",
            poly_area=0.0939,
            polygon=[[0.7613, 0.3252], [1.0, 0.4374], [0.9387, 0.8551], [0.6975, 0.7685]],
            label="module",
        )

        self.assertEqual(vertical, ["B1", "C1"])
        self.assertEqual(horizontal, ["C3"])

    def test_low_confidence_detection_marks_slot_uncertain(self) -> None:
        det = {
            "detection_id": 1,
            "label": "module",
            "confidence": 0.3,
            "confidence_band": "low",
            "reasons": ["low_confidence_detection"],
            "mapping_notes": [],
            "needs_human_review": True,
            "assignable_to_slots": True,
        }

        slot_observations, _ = _build_slot_observations(
            {"A1": [det]},
            slot_mapping_method="deck_homography",
            obs_source="trained_yolo",
            coco_untrusted=False,
        )

        self.assertEqual(slot_observations["A1"]["state"], "uncertain")
        self.assertIn("low_confidence_detection", slot_observations["A1"]["reasons"])

    def test_homography_low_confidence_single_label_can_be_promoted(self) -> None:
        det = {
            "detection_id": 1,
            "label": "module",
            "confidence": 0.42,
            "confidence_band": "low",
            "reasons": ["low_confidence_detection", "coverage_spans_multiple_slots"],
            "mapping_notes": [],
            "needs_human_review": True,
            "assignable_to_slots": True,
        }

        slot_observations, _ = _build_slot_observations(
            {"A1": [det]},
            slot_mapping_method="deck_homography",
            obs_source="trained_yolo",
            coco_untrusted=False,
        )

        self.assertEqual(slot_observations["A1"]["state"], "occupied")
        self.assertIn("promoted_from_reviewable_detection", slot_observations["A1"]["reasons"])

    def test_high_confidence_boundary_detection_can_be_promoted(self) -> None:
        det = {
            "detection_id": 1,
            "label": "tiprack",
            "confidence": 0.84,
            "confidence_band": "high",
            "reasons": ["near_slot_boundary"],
            "mapping_notes": [],
            "needs_human_review": True,
            "assignable_to_slots": True,
        }

        slot_observations, _ = _build_slot_observations(
            {"C2": [det]},
            slot_mapping_method="deck_homography",
            obs_source="trained_yolo",
            coco_untrusted=False,
        )

        self.assertEqual(slot_observations["C2"]["state"], "occupied")
        self.assertIn("promoted_from_reviewable_detection", slot_observations["C2"]["reasons"])

    def test_empty_slot_is_uncertain_under_uniform_grid_fallback(self) -> None:
        slot_observations, _ = _build_slot_observations(
            {},
            slot_mapping_method="uniform_image_grid",
            obs_source="trained_yolo",
            coco_untrusted=False,
        )

        self.assertEqual(slot_observations["B2"]["state"], "uncertain")
        self.assertIn("uniform_grid_fallback", slot_observations["B2"]["reasons"])

    def test_expected_layout_mismatch_downgrades_slot_to_uncertain(self) -> None:
        slot_observations = {
            "A1": {
                "state": "occupied",
                "source": "trained_yolo",
                "label": "plate",
                "labels": None,
                "confidence": 0.91,
                "confidence_band": "high",
                "reasons": [],
                "covered_by": [1],
                "detection_count": 1,
            }
        }

        mismatches = _compute_mismatches({"A1": "module"}, slot_observations)
        _apply_mismatch_flags(slot_observations, mismatches)

        self.assertEqual(mismatches[0]["reason"], "label_mismatch")
        self.assertEqual(slot_observations["A1"]["state"], "uncertain")
        self.assertIn("expected_layout_mismatch", slot_observations["A1"]["reasons"])

    def test_extract_deck_quad_norm_supports_legacy_multi_point_polygon(self) -> None:
        legacy_path = ROOT.parent / "labagentyolo" / "data" / "frames" / "samples" / "deck_vid3_02.json"
        data = json.loads(legacy_path.read_text(encoding="utf-8"))

        corners = extract_deck_quad_norm(data)

        self.assertIsNotNone(corners)
        self.assertEqual(len(corners), 4)
        self.assertEqual(len({tuple(round(v, 5) for v in point) for point in corners}), 4)

    def test_pick_ordered_deck_corners_normalizes_wrong_four_point_order(self) -> None:
        wrong_order = [
            [0.40, 0.25],  # A1
            [0.37, 0.61],  # actually D1
            [0.61, 0.60],  # D3
            [0.60, 0.34],  # actually A3
        ]

        ordered = _pick_ordered_deck_corners(wrong_order)

        self.assertEqual(
            ordered,
            [
                [0.40, 0.25],
                [0.60, 0.34],
                [0.61, 0.60],
                [0.37, 0.61],
            ],
        )


if __name__ == "__main__":
    unittest.main()
