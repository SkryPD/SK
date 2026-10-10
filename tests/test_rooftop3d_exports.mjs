import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { buildModelDescriptors, loadTruthScene } from "../src/rooftop3d/model.mjs";
import {
  exportUniversalPackage,
  parseGlbJson,
} from "../src/rooftop3d/exporters.mjs";

test("universal export writes parseable GLB, millimetre OBJ/MTL and manifest", async (t) => {
  const outDir = await mkdtemp(join(tmpdir(), "rooftop3d-export-"));
  t.after(() => rm(outDir, { recursive: true, force: true }));

  const model = buildModelDescriptors(loadTruthScene());
  const result = await exportUniversalPackage(model, outDir);
  const [glb, objText, mtlText, manifestText] = await Promise.all([
    readFile(result.glbPath),
    readFile(result.objPath, "utf8"),
    readFile(result.mtlPath, "utf8"),
    readFile(result.manifestPath, "utf8"),
  ]);

  assert.equal(glb.readUInt32LE(0), 0x46546c67);
  assert.equal(glb.readUInt32LE(4), 2);
  assert.equal(glb.readUInt32LE(8), glb.length);

  const glbJson = parseGlbJson(glb);
  const teaWallNode = glbJson.nodes.find((node) => node.name === "tea_background_wall");
  assert.ok(teaWallNode);
  assert.equal(teaWallNode.extras.layer, "approved_fixed_design");
  assert.equal(teaWallNode.extras.status, "verified");
  assert.deepEqual(teaWallNode.extras.bounds_mm, [37320, 6160, 37440, 10260]);
  assert.ok(glbJson.nodes.some((node) => node.name === "bar_body_fixed_run"));
  assert.ok(glbJson.nodes.some((node) => node.name === "E5"));

  assert.match(objText, /^mtllib rooftop_truth_model_v01\.mtl/m);
  assert.match(objText, /^g tea_background_wall$/m);
  assert.match(objText, /^usemtl wall_verified$/m);
  assert.match(objText, /^v 37320 0 6160$/m);
  assert.match(objText, /^f \d+(?:\/\d*\/\d+)? \d+(?:\/\d*\/\d+)? \d+(?:\/\d*\/\d+)?$/m);
  assert.match(mtlText, /^newmtl wall_verified$/m);

  const manifest = JSON.parse(manifestText);
  assert.equal(manifest.version, "rooftop-universal-3d-package-v01");
  assert.equal(manifest.coordinate_system.glb_units, "metres");
  assert.equal(manifest.coordinate_system.obj_units, "millimetres");
  assert.equal(manifest.coordinate_system.up_axis, "Y");
  assert.equal(manifest.candidate_status, "candidate_requires_clash_decision");
  assert.equal(manifest.design_clashes[0].overlap_mm, 300);
  assert.deepEqual(manifest.layers.existing_roof_truss.object_ids, []);
  assert.deepEqual(manifest.layers.future_glass_system.object_ids, []);
  assert.equal(manifest.source.sha256.length, 64);
  assert.equal(manifest.objects.find((item) => item.id === "tea_room_floor").kind, "floor_plane");
  assert.deepEqual(manifest.unhandled_source_objects, []);

  for (const file of Object.values(manifest.files)) {
    assert.ok(file.bytes > 0);
    assert.equal(file.sha256.length, 64);
  }
});

test("parseGlbJson rejects a non-GLB buffer", () => {
  assert.throws(() => parseGlbJson(Buffer.from("not a glb")), /Invalid GLB header/);
});
