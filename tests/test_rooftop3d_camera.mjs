import test from "node:test";
import assert from "node:assert/strict";

import { fitDistanceForBounds } from "../src/rooftop3d/viewer/camera.mjs";

test("fitDistanceForBounds contains the full rooftop bounding sphere on desktop", () => {
  const distance = fitDistanceForBounds(
    { x: 37.64, y: 3.02, z: 13.16 },
    46,
    1136 / 1000,
  );
  assert.ok(distance > 57 && distance < 58);
});

test("fitDistanceForBounds increases distance for a narrow mobile viewport", () => {
  const desktop = fitDistanceForBounds({ x: 37.64, y: 3.02, z: 13.16 }, 46, 1.136);
  const mobile = fitDistanceForBounds({ x: 37.64, y: 3.02, z: 13.16 }, 46, 390 / 844);
  assert.ok(mobile > desktop * 2);
});

test("fitDistanceForBounds rejects invalid dimensions and camera values", () => {
  assert.throws(() => fitDistanceForBounds({ x: 0, y: 0, z: 0 }, 46, 1), /positive finite/);
  assert.throws(() => fitDistanceForBounds({ x: 1, y: 1, z: 1 }, 0, 1), /field of view/);
  assert.throws(() => fitDistanceForBounds({ x: 1, y: 1, z: 1 }, 46, 0), /aspect ratio/);
});
