import test from "node:test";
import assert from "node:assert/strict";

import { setLayerVisibility } from "../src/rooftop3d/viewer/layers.mjs";

test("setLayerVisibility updates a layer and every descendant", () => {
  const grandchild = { visible: false, children: [] };
  const child = { visible: false, children: [grandchild] };
  const layer = { visible: false, children: [child] };

  setLayerVisibility(layer, true);

  assert.equal(layer.visible, true);
  assert.equal(child.visible, true);
  assert.equal(grandchild.visible, true);

  setLayerVisibility(layer, false);

  assert.equal(layer.visible, false);
  assert.equal(child.visible, false);
  assert.equal(grandchild.visible, false);
});
