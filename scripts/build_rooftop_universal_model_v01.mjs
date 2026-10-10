import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";

import {
  buildModelDescriptors,
  loadTruthScene,
  ROOT,
  validateModel,
  V04_SOURCE_PATH,
} from "../src/rooftop3d/model.mjs";
import { exportUniversalPackage } from "../src/rooftop3d/exporters.mjs";

export const OUTPUT_DIR = resolve(
  ROOT,
  "output/空间真值/三维模型/候选_v01_20261010",
);

const VIEWER_SOURCE_DIR = resolve(ROOT, "src/rooftop3d/viewer");
const THREE_PACKAGE_DIR = resolve(ROOT, "tools/rooftop3d-web/node_modules/three");
const LUCIDE_ICON_DIR = resolve(ROOT, "tools/rooftop3d-web/node_modules/lucide-static/icons");

async function buildViewer(outDir) {
  const viewerDir = resolve(outDir, "viewer");
  const vendorDir = resolve(viewerDir, "vendor");
  const iconDir = resolve(vendorDir, "icons");
  const utilsDir = resolve(viewerDir, "utils");
  await Promise.all([
    mkdir(iconDir, { recursive: true }),
    mkdir(utilsDir, { recursive: true }),
  ]);
  const copies = [
    [resolve(VIEWER_SOURCE_DIR, "index.html"), resolve(viewerDir, "index.html")],
    [resolve(VIEWER_SOURCE_DIR, "styles.css"), resolve(viewerDir, "styles.css")],
    [resolve(VIEWER_SOURCE_DIR, "app.js"), resolve(viewerDir, "app.js")],
    [resolve(VIEWER_SOURCE_DIR, "camera.mjs"), resolve(viewerDir, "camera.mjs")],
    [resolve(THREE_PACKAGE_DIR, "build/three.module.js"), resolve(vendorDir, "three.module.js")],
    [resolve(THREE_PACKAGE_DIR, "build/three.core.js"), resolve(vendorDir, "three.core.js")],
    [resolve(THREE_PACKAGE_DIR, "examples/jsm/controls/OrbitControls.js"), resolve(vendorDir, "OrbitControls.js")],
    [resolve(THREE_PACKAGE_DIR, "examples/jsm/loaders/GLTFLoader.js"), resolve(vendorDir, "GLTFLoader.js")],
    [resolve(THREE_PACKAGE_DIR, "examples/jsm/utils/BufferGeometryUtils.js"), resolve(utilsDir, "BufferGeometryUtils.js")],
    [resolve(THREE_PACKAGE_DIR, "examples/jsm/utils/SkeletonUtils.js"), resolve(utilsDir, "SkeletonUtils.js")],
    [resolve(THREE_PACKAGE_DIR, "LICENSE"), resolve(vendorDir, "THREE-LICENSE.txt")],
    [resolve(LUCIDE_ICON_DIR, "maximize.svg"), resolve(iconDir, "maximize.svg")],
    [resolve(LUCIDE_ICON_DIR, "rotate-ccw.svg"), resolve(iconDir, "rotate-ccw.svg")],
    [resolve(LUCIDE_ICON_DIR, "panel-left.svg"), resolve(iconDir, "panel-left.svg")],
  ];
  await Promise.all(copies.map(([source, destination]) => copyFile(source, destination)));
  const threeCorePath = resolve(vendorDir, "three.core.js");
  const normalizedThreeCore = (await readFile(threeCorePath, "utf8")).replaceAll(" \t", "\t");
  await writeFile(threeCorePath, normalizedThreeCore, "utf8");
  const indexPath = resolve(viewerDir, "index.html");
  const index = (await readFile(indexPath, "utf8"))
    .replace('data-model-version="v02"', 'data-model-version="v01"')
    .replaceAll("楼顶空间真值模型 v02", "楼顶空间真值模型 v01")
    .replace("候选 v02", "候选 v01")
    .replace('class="clash-flag is-resolved"', 'class="clash-flag"')
    .replace("窗洞封顶已确认", "窗顶 / 天花冲突")
    .replace("Z 2450", "300 mm");
  await writeFile(indexPath, index, "utf8");
  return viewerDir;
}

export async function buildPackage(outDir = OUTPUT_DIR) {
  const source = loadTruthScene(V04_SOURCE_PATH);
  const model = buildModelDescriptors(source);
  const errors = validateModel(model);
  if (errors.length > 0) {
    throw new Error(`Model validation failed:\n${errors.join("\n")}`);
  }
  const exported = await exportUniversalPackage(model, outDir, { sourcePath: V04_SOURCE_PATH });
  const viewerDir = await buildViewer(outDir);
  return { ...exported, viewerDir };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = await buildPackage();
  console.log(`GLB: ${result.glbPath}`);
  console.log(`OBJ: ${result.objPath}`);
  console.log(`MTL: ${result.mtlPath}`);
  console.log(`Manifest: ${result.manifestPath}`);
  console.log(`Viewer: ${result.viewerDir}`);
}
