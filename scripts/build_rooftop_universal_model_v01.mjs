import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

import {
  buildModelDescriptors,
  loadTruthScene,
  ROOT,
  validateModel,
} from "../src/rooftop3d/model.mjs";
import { exportUniversalPackage } from "../src/rooftop3d/exporters.mjs";

export const OUTPUT_DIR = resolve(
  ROOT,
  "output/空间真值/三维模型/候选_v01_20261010",
);

export async function buildPackage(outDir = OUTPUT_DIR) {
  const source = loadTruthScene();
  const model = buildModelDescriptors(source);
  const errors = validateModel(model);
  if (errors.length > 0) {
    throw new Error(`Model validation failed:\n${errors.join("\n")}`);
  }
  return exportUniversalPackage(model, outDir);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = await buildPackage();
  console.log(`GLB: ${result.glbPath}`);
  console.log(`OBJ: ${result.objPath}`);
  console.log(`MTL: ${result.mtlPath}`);
  console.log(`Manifest: ${result.manifestPath}`);
}
