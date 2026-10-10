import test from "node:test";
import assert from "node:assert/strict";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { buildPackage as buildV01Package } from "../scripts/build_rooftop_universal_model_v01.mjs";
import { buildPackage as buildV02Package } from "../scripts/build_rooftop_universal_model_v02.mjs";

test("v02 buildPackage creates a fully offline responsive Three.js viewer", async (t) => {
  const outDir = await mkdtemp(join(tmpdir(), "rooftop3d-viewer-"));
  t.after(() => rm(outDir, { recursive: true, force: true }));
  await buildV02Package(outDir);

  const viewerDir = join(outDir, "viewer");
  const [html, css, app, threeCore] = await Promise.all([
    readFile(join(viewerDir, "index.html"), "utf8"),
    readFile(join(viewerDir, "styles.css"), "utf8"),
    readFile(join(viewerDir, "app.js"), "utf8"),
    readFile(join(viewerDir, "vendor", "three.core.js"), "utf8"),
  ]);

  assert.match(html, /id="viewport"/);
  assert.match(html, /data-model-version="v02"/);
  assert.match(html, /候选 v02/);
  assert.match(html, /窗洞封顶已确认/);
  assert.match(html, /id="layer-list"/);
  assert.match(html, /id="object-details"/);
  assert.match(html, /aria-label="切换控制面板"/);
  assert.match(html, /data-view="plan"/);
  assert.match(html, /data-view="isometric"/);
  assert.match(html, /data-view="V01-R1"/);
  assert.match(html, /data-view="V02-R1"/);
  assert.match(html, /\.\/vendor\/icons\/maximize\.svg/);
  assert.match(html, /"three": "\.\/vendor\/three\.module\.js"/);

  assert.match(app, /dataset\.modelVersion/);
  assert.match(app, /rooftop_truth_model_\$\{MODEL_VERSION\}\.glb/);
  assert.match(app, /design_ceiling/);
  assert.match(app, /V01-R1/);
  assert.match(app, /V02-R1/);
  assert.match(app, /Raycaster/);
  assert.match(app, /function isObjectVisibleInHierarchy\(object\)/);
  assert.match(app, /item\.object\.userData\.id && isObjectVisibleInHierarchy\(item\.object\)/);
  assert.match(app, /Object\.hasOwn\(LAYER_LABELS, object\.name\)/);
  assert.match(app, /dataset\.viewerReady = "true"/);
  assert.doesNotMatch(app, /PCFSoftShadowMap/);
  assert.match(css, /@media \(max-width: 720px\)/);
  assert.match(css, /\.panel-collapsed/);
  assert.match(css, /@media \(max-width: 720px\)[\s\S]*?\.control-panel \{[\s\S]*?overflow-y: auto;/);

  assert.doesNotMatch(`${html}\n${css}\n${app}`, /https?:\/\//);
  assert.doesNotMatch(threeCore, / \t/, "vendored viewer files should pass git whitespace checks");
  const requiredVendorFiles = [
    "camera.mjs",
    "vendor/three.module.js",
    "vendor/three.core.js",
    "vendor/OrbitControls.js",
    "vendor/GLTFLoader.js",
    "utils/BufferGeometryUtils.js",
    "utils/SkeletonUtils.js",
    "vendor/THREE-LICENSE.txt",
    "vendor/icons/maximize.svg",
    "vendor/icons/rotate-ccw.svg",
    "vendor/icons/panel-left.svg",
  ];
  await Promise.all(requiredVendorFiles.map((path) => access(join(viewerDir, path))));
});

test("historical v01 package still emits a v01 viewer target", async (t) => {
  const outDir = await mkdtemp(join(tmpdir(), "rooftop3d-viewer-v01-"));
  t.after(() => rm(outDir, { recursive: true, force: true }));
  await buildV01Package(outDir);

  const html = await readFile(join(outDir, "viewer", "index.html"), "utf8");
  const threeCore = await readFile(join(outDir, "viewer", "vendor", "three.core.js"), "utf8");
  assert.match(html, /data-model-version="v01"/);
  assert.match(html, /候选 v01/);
  assert.doesNotMatch(threeCore, / \t/);
  await access(join(outDir, "rooftop_truth_model_v01.glb"));
});
