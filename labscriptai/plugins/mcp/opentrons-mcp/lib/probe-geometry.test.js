import test from "node:test";
import assert from "node:assert/strict";

import {
  defaultLiquidRoleForLabware,
  heightMmToVolumeUl,
  lookupLabwareGeometry,
} from "./probe.js";

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

test("nest_96_wellplate_200ul_flat approximate geometry is registered", () => {
  const geometry = lookupLabwareGeometry("nest_96_wellplate_200ul_flat");
  assert.ok(geometry);
  assert.equal(geometry.shape, "conical");
  assert.equal(geometry.well_depth_mm, 10.8);
  assert.equal(geometry.capacity_ul, 200);
  assert.equal(geometry.approximate, true);
});

test("heightMmToVolumeUl estimates nest_96 flat destination volume from height", () => {
  const converted = heightMmToVolumeUl({
    height_mm: 5.4,
    labware_load_name: "nest_96_wellplate_200ul_flat",
  });
  assert.equal(converted.method, "geometry:approximate:nest_96_wellplate_200ul_flat");
  assert.ok(converted.volume_ul > 100);
  assert.ok(converted.volume_ul < 200);
});

test("heightMmToVolumeUl clamps nest_96 flat overflow to capacity", () => {
  const converted = heightMmToVolumeUl({
    height_mm: 20,
    labware_load_name: "nest_96_wellplate_200ul_flat",
  });
  assert.equal(converted.volume_ul, 200);
  assert.match(String(converted.notes || ""), /height_exceeds_well_depth_clamped/);
});

test("defaultLiquidRoleForLabware maps bench plate to destination", () => {
  assert.equal(defaultLiquidRoleForLabware("nest_96_wellplate_200ul_flat"), "destination");
  assert.equal(defaultLiquidRoleForLabware("nest_12_reservoir_15ml"), "source");
  assert.equal(defaultLiquidRoleForLabware("opentrons_flex_96_tiprack_1000ul"), null);
});
