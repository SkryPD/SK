import test from "node:test";
import assert from "node:assert/strict";

import {
  buildModelDescriptors,
  loadTruthScene,
  validateModel,
} from "../src/rooftop3d/model.mjs";

test("v04 truth scene builds the approved rooftop geometry contract", () => {
  const source = loadTruthScene();
  const model = buildModelDescriptors(source);
  const byId = new Map(model.objects.map((item) => [item.id, item]));

  assert.equal(source.version, "rooftop-whole-floor-truth-model-v04");
  assert.equal(model.candidate_status, "candidate_requires_clash_decision");
  assert.deepEqual(model.topology.points_mm.C, [34240, 6160]);
  assert.deepEqual(byId.get("tea_room_floor").bounds_mm, [34240, 6160, 37440, 10260]);
  assert.equal(model.objects.filter((item) => item.kind === "steel_column").length, 4);

  assert.deepEqual(byId.get("bar_flip_gate").bounds_mm, [35040, 1130, 35840, 1930]);
  assert.deepEqual(byId.get("bar_body_fixed_run").bounds_mm, [35040, 1930, 35840, 6160]);
  assert.equal(byId.has("bar_body"), false);

  assert.deepEqual(model.equipment.map((item) => item.id), ["E1", "E2", "E3", "E4", "E5"]);
  assert.equal(model.equipment.reduce((sum, item) => sum + item.length_mm, 0), 4400);
  assert.deepEqual(byId.get("E1").bounds_mm, [36840, 1760, 37440, 2760]);
  assert.deepEqual(byId.get("E5").bounds_mm, [36640, 5160, 37440, 6160]);
  assert.equal(byId.has("equipment_run"), false);
  assert.equal(byId.has("equipment_rack"), false);

  assert.deepEqual(model.layers.existing_roof_truss, {
    default_visible: false,
    object_ids: [],
    status: "requires_site_measurement",
  });
  assert.deepEqual(model.layers.future_glass_system, {
    default_visible: false,
    object_ids: [],
    status: "requires_site_measurement",
  });
  assert.equal(model.clashes[0].id, "tea_window_head_vs_ceiling");
  assert.equal(model.clashes[0].overlap_mm, 300);
  assert.deepEqual(validateModel(model), []);
});

test("loadTruthScene rejects any source version other than v04", () => {
  assert.throws(
    () => loadTruthScene(new URL("./fixtures/not-v04.json", import.meta.url)),
    /Unsupported rooftop truth scene version: test-version/,
  );
});

test("validateModel reports broken topology and non-finite geometry", () => {
  const model = buildModelDescriptors(loadTruthScene());
  const broken = structuredClone(model);
  broken.topology.points_mm.C = [Number.NaN, 6160];
  broken.objects.find((item) => item.id === "tea_room_floor").bounds_mm[2] = Infinity;

  const errors = validateModel(broken);
  assert.ok(errors.some((error) => error.includes("A/C/B must be finite and collinear")));
  assert.ok(errors.some((error) => error.includes("tea_room_floor has non-finite bounds")));
});
