import test from "node:test";
import assert from "node:assert/strict";

import { heightMmToVolumeUl, lookupLabwareGeometry } from "./probe.js";

test("nest_12_reservoir_15ml approximate geometry is registered", () => {
  const geometry = lookupLabwareGeometry("nest_12_reservoir_15ml");
  assert.ok(geometry);
  assert.equal(geometry.well_depth_mm, 26.85);
  assert.equal(geometry.capacity_ul, 15000);
  assert.equal(geometry.approximate, true);
  assert.ok(Math.abs(geometry.cross_section_area_mm2 - 8.2 * 71.2) < 1e-9);
});

test("heightMmToVolumeUl estimates nest_12 trough volume from height", () => {
  const converted = heightMmToVolumeUl({
    height_mm: 16.11,
    labware_load_name: "nest_12_reservoir_15ml",
  });
  assert.equal(converted.method, "geometry:approximate:nest_12_reservoir_15ml");
  // 8.2 * 71.2 * 16.11 ≈ 9405.7
  assert.ok(converted.volume_ul > 9000);
  assert.ok(converted.volume_ul < 9800);
});

test("heightMmToVolumeUl clamps nest_12 overflow to capacity", () => {
  const converted = heightMmToVolumeUl({
    height_mm: 40,
    labware_load_name: "nest_12_reservoir_15ml",
  });
  assert.equal(converted.volume_ul, 15000);
});

test("heightMmToVolumeUl returns 0 for non-positive height", () => {
  const converted = heightMmToVolumeUl({
    height_mm: 0,
    labware_load_name: "nest_12_reservoir_15ml",
  });
  assert.equal(converted.volume_ul, 0);
});
