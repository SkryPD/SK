# Rooftop Ceiling Viewer v03 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user-supplied `AGENTS.md` forbids subagents, so execute inline in the current thread.

**Goal:** Build a non-destructive v03 offline viewer candidate with a reliable full-floor ceiling inspection preset and verified screenshots.

**Architecture:** Keep the v02 GLB geometry unchanged. Add a small recursive layer-visibility helper, wire it into manual controls and a new ceiling preset, then package the revised viewer beside the existing v02 candidate. Verify behavior in unit tests and in the real browser before producing the candidate report.

**Tech Stack:** JavaScript ES modules, Three.js, Node test runner, offline HTML/CSS viewer, browser visual verification

---

### Task 1: Lock recursive layer visibility with a failing test

**Files:**
- Create: `src/rooftop3d/viewer/layers.mjs`
- Create: `tests/test_rooftop3d_layers.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
import { setLayerVisibility } from "../src/rooftop3d/viewer/layers.mjs";

test("setLayerVisibility updates a layer and every descendant", () => {
  const child = { visible: false, children: [] };
  const layer = { visible: false, children: [child] };
  setLayerVisibility(layer, true);
  assert.equal(layer.visible, true);
  assert.equal(child.visible, true);
  setLayerVisibility(layer, false);
  assert.equal(layer.visible, false);
  assert.equal(child.visible, false);
});
```

- [ ] **Step 2: Run RED**

Run: `node --test tests/test_rooftop3d_layers.mjs`

Expected: FAIL because `layers.mjs` does not exist.

- [ ] **Step 3: Implement the minimal recursive helper**

```javascript
export function setLayerVisibility(layer, visible) {
  layer.visible = visible;
  for (const child of layer.children ?? []) {
    setLayerVisibility(child, visible);
  }
}
```

- [ ] **Step 4: Run GREEN**

Run: `node --test tests/test_rooftop3d_layers.mjs`

Expected: 1 test passed, 0 failed.

### Task 2: Add and test the ceiling-inspection preset

**Files:**
- Modify: `src/rooftop3d/viewer/index.html`
- Modify: `src/rooftop3d/viewer/app.js`
- Modify: `src/rooftop3d/viewer/styles.css`
- Modify: `src/rooftop3d/three-scene.mjs`
- Modify: `tests/test_rooftop3d_viewer.mjs`

- [ ] **Step 1: Extend the viewer test first**

```javascript
assert.match(html, /data-view="ceiling"/);
assert.match(html, /封顶核验/);
assert.match(app, /setLayerVisibility/);
assert.match(app, /name === "ceiling"/);
assert.match(app, /setLayerChecked\("design_ceiling", name === "ceiling"\)/);
```

- [ ] **Step 2: Run the viewer test and observe failure**

Run: `node --test tests/test_rooftop3d_viewer.mjs`

Expected: FAIL because the ceiling preset is absent.

- [ ] **Step 3: Implement the preset**

Add a full-width `封顶核验` button, import `setLayerVisibility`, keep a layer-control map, synchronize the checkbox and hierarchy through `setLayerChecked()`, and add a high-angle `ceiling` camera pose. Other presets call `setLayerChecked("design_ceiling", false)`.

- [ ] **Step 4: Strengthen ceiling material visibility**

Change `ceiling_plane_owner_confirmed` to a warm neutral material around 55–65% opacity. Keep it double-sided and transparent; do not add thickness.

- [ ] **Step 5: Run all rooftop unit tests**

Run: `node --test tests/test_rooftop3d_camera.mjs tests/test_rooftop3d_exports.mjs tests/test_rooftop3d_layers.mjs tests/test_rooftop3d_scene.mjs tests/test_rooftop3d_viewer.mjs`

Expected: all tests pass with zero failures.

### Task 3: Build the non-destructive v03 viewer candidate

**Files:**
- Create: `scripts/build_rooftop_universal_model_v03.mjs`
- Modify: `tests/test_rooftop3d_viewer.mjs`
- Create: `output/空间真值/三维模型/候选_v03_20261011/`

- [ ] **Step 1: Add a failing package test**

```javascript
const result = await buildV03Package(outDir);
const html = await readFile(join(result.viewerDir, "index.html"), "utf8");
assert.match(html, /候选 v03/);
assert.match(html, /data-model-version="v02"/);
await access(join(outDir, "rooftop_truth_model_v02.glb"));
await access(join(result.viewerDir, "layers.mjs"));
```

- [ ] **Step 2: Run RED**

Run: `node --test tests/test_rooftop3d_viewer.mjs`

Expected: FAIL because the v03 builder does not exist.

- [ ] **Step 3: Implement the v03 builder**

Call the v02 geometry exporter into `候选_v03_20261011`, copy `layers.mjs`, and relabel only the candidate viewer revision. Preserve `data-model-version="v02"` and the v02 geometry filenames.

- [ ] **Step 4: Build the package**

Run: `node scripts/build_rooftop_universal_model_v03.mjs`

Expected: GLB, OBJ, MTL, manifest and offline viewer exist under the v03 candidate directory.

### Task 4: Browser verification, screenshot and report

**Files:**
- Create: `output/空间真值/三维模型/候选_v03_20261011/核验截图/05_整层封顶核验.jpg`
- Create: `output/空间真值/三维模型/候选_v03_20261011/楼顶通用三维模型_v03_封顶核验报告.md`
- Create: `output/空间真值/三维模型/候选_v03_20261011/README_查看器v03与模型v02版本边界.md`

- [ ] **Step 1: Start a local HTTP server and open the v03 viewer**

Serve the candidate directory on a free localhost port. Open `/viewer/`, wait for `window.__rooftopViewerReady === true`, then select `封顶核验`.

- [ ] **Step 2: Verify real browser state**

Confirm the `design_ceiling` checkbox is checked, its parent group is visible, both ceiling descendants are visible, the console contains zero errors, and switching to `轴测` hides all three again.

- [ ] **Step 3: Capture and inspect desktop and mobile screenshots**

Capture a desktop `封顶核验` view as the formal candidate screenshot. At `390 x 844`, confirm there is no page overflow or incoherent text/control overlap. Open the desktop image and perform a nonblank/non-monochrome pixel check.

- [ ] **Step 4: Write the report and README**

Record geometry-version boundaries, the pass/fail matrix, screenshot hash, test totals and the non-construction disclaimer.

- [ ] **Step 5: Final verification and scoped commit**

Run the full rooftop Node suite, `git diff --check`, inspect staged names, and commit only v03-related source, tests, docs and output files.
