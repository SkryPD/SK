import test from "node:test";
import assert from "node:assert/strict";
import {
  calculateQuantities,
  defaultQuantityInputs,
} from "../src/spa_procurement/quantity_model.mjs";

test("drawing inputs preserve the approved spa geometry", () => {
  assert.equal(defaultQuantityInputs.poolCount, 2);
  assert.equal(defaultQuantityInputs.poolLengthM, 8.18);
  assert.equal(defaultQuantityInputs.poolWidthM, 4.24);
  assert.equal(defaultQuantityInputs.poolFinishedDepthM, 0.85);
  assert.equal(defaultQuantityInputs.ceilingGrossWidthM, 14.718);
  assert.equal(defaultQuantityInputs.ceilingGrossLengthM, 13.3);
});

test("tile and ceiling quantities are transparent and reproducible", () => {
  const q = calculateQuantities();
  assert.equal(q.poolBottomM2, 69.3664);
  assert.equal(q.poolWallM2, 42.228);
  assert.equal(q.poolCopingM2, 12.92);
  assert.equal(q.bathDeckFloorM2, 31.9424);
  assert.equal(q.supportFloorM2, 66.3001);
  assert.equal(q.wallTileGrossM2, 253.5984);
  assert.equal(q.generalWallTileM2, 237.5984);
  assert.equal(q.featureWallTileM2, 16);
  assert.equal(q.ceilingGrossM2, 195.7494);
  assert.equal(q.woodgrainUpgradeM2, 29.3624);
  assert.equal(q.poolStepAllowanceM2, 18);
});

test("lighting placeholders remain explicit budget assumptions", () => {
  const q = calculateQuantities();
  assert.deepEqual(q.lighting, {
    downlightsEach: 32,
    linearLightM: 40,
    wallWashersEach: 4,
    lightingDriversEach: 6,
  });
  assert.equal(q.accessHatchesEach, 6);
});
