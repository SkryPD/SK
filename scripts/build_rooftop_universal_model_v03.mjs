import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { ROOT } from "../src/rooftop3d/model.mjs";
import { buildPackage as buildV02Package } from "./build_rooftop_universal_model_v02.mjs";

export const OUTPUT_DIR = resolve(
  ROOT,
  "output/空间真值/三维模型/候选_v03_20261011",
);

export async function buildPackage(outDir = OUTPUT_DIR) {
  const result = await buildV02Package(outDir);
  const indexPath = resolve(result.viewerDir, "index.html");
  const source = await readFile(indexPath, "utf8");
  const index = source
    .replace(
      '<html lang="zh-CN" data-model-version="v02">',
      '<html lang="zh-CN" data-model-version="v02" data-viewer-version="v03">',
    )
    .replace(
      "<title>楼顶空间真值模型 v02</title>",
      "<title>楼顶空间真值模型 v02 · 封顶核验查看器 v03</title>",
    )
    .replace("候选 v02", "候选 v03")
    .replace("<p>非施工放样模型</p>", "<p>模型 v02 · 查看器 v03 · 非施工放样</p>");
  await writeFile(indexPath, index, "utf8");

  return {
    ...result,
    modelVersion: "v02",
    viewerVersion: "v03",
  };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = await buildPackage();
  console.log(`GLB: ${result.glbPath}`);
  console.log(`OBJ: ${result.objPath}`);
  console.log(`MTL: ${result.mtlPath}`);
  console.log(`Manifest: ${result.manifestPath}`);
  console.log(`Viewer: ${result.viewerDir}`);
  console.log(`Version boundary: model ${result.modelVersion}, viewer ${result.viewerVersion}`);
}
