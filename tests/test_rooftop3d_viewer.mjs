import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { access, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { buildPackage as buildV01Package } from "../scripts/build_rooftop_universal_model_v01.mjs";
import {
  buildPackage as buildV02Package,
  OUTPUT_DIR as V02_OUTPUT_DIR,
} from "../scripts/build_rooftop_universal_model_v02.mjs";
import { buildPackage as buildV03Package } from "../scripts/build_rooftop_universal_model_v03.mjs";

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
  assert.match(html, /data-view="ceiling"/);
  assert.match(html, /封顶核验/);
  assert.match(html, /\.\/vendor\/icons\/maximize\.svg/);
  assert.match(html, /"three": "\.\/vendor\/three\.module\.js"/);

  assert.match(app, /dataset\.modelVersion/);
  assert.match(app, /rooftop_truth_model_\$\{MODEL_VERSION\}\.glb/);
  assert.match(app, /design_ceiling/);
  assert.match(app, /setLayerVisibility/);
  assert.match(app, /function setLayerChecked\(layerId, checked\)/);
  assert.match(app, /name === "ceiling"/);
  assert.match(app, /setLayerChecked\("design_ceiling", name === "ceiling"\)/);
  assert.match(app, /function setCeilingPose\(\)/);
  assert.match(app, /function styleCeilingLayer\(\)/);
  assert.match(app, /material\.color\.set\(0xb8ada0\)/);
  assert.match(app, /material\.opacity = 0\.62/);
  assert.match(app, /new THREE\.Box3\(\)\.setFromObject\(ceilingLayer\)/);
  assert.match(app, /fitDistanceForBounds\(ceilingSize, 42, viewportAspect\(\), 1\.16\)/);
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
  assert.match(css, /\.ceiling-view/);
  assert.match(css, /@media \(max-width: 720px\)[\s\S]*?\.control-panel \{[\s\S]*?overflow-y: auto;/);

  assert.doesNotMatch(`${html}\n${css}\n${app}`, /https?:\/\//);
  assert.doesNotMatch(threeCore, / \t/, "vendored viewer files should pass git whitespace checks");
  const requiredVendorFiles = [
    "camera.mjs",
    "layers.mjs",
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
  await access(join(outDir, "viewer", "layers.mjs"));
});

test("v03 package revises only the viewer while preserving v02 geometry", async (t) => {
  const outDir = await mkdtemp(join(tmpdir(), "rooftop3d-viewer-v03-"));
  t.after(() => rm(outDir, { recursive: true, force: true }));

  const result = await buildV03Package(outDir);
  const html = await readFile(join(result.viewerDir, "index.html"), "utf8");

  assert.match(html, /data-model-version="v02"/);
  assert.match(html, /data-viewer-version="v03"/);
  assert.match(html, /候选 v03/);
  assert.match(html, /模型 v02 · 查看器 v03 · 非施工放样/);
  assert.equal(result.modelVersion, "v02");
  assert.equal(result.viewerVersion, "v03");
  const [v02Glb, v03Glb] = await Promise.all([
    readFile(join(V02_OUTPUT_DIR, "rooftop_truth_model_v02.glb")),
    readFile(join(outDir, "rooftop_truth_model_v02.glb")),
  ]);
  assert.equal(
    createHash("sha256").update(v03Glb).digest("hex"),
    createHash("sha256").update(v02Glb).digest("hex"),
  );
  await access(join(result.viewerDir, "layers.mjs"));
});
