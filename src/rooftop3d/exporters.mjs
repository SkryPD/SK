import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";

import { GLTFExporter } from "../../tools/rooftop3d-web/node_modules/three/examples/jsm/exporters/GLTFExporter.js";
import { OBJExporter } from "../../tools/rooftop3d-web/node_modules/three/examples/jsm/exporters/OBJExporter.js";
import { SOURCE_PATH, validateModel } from "./model.mjs";
import { createThreeScene, MATERIAL_DEFINITIONS } from "./three-scene.mjs";

const FILENAMES = {
  glb: "rooftop_truth_model_v01.glb",
  obj: "rooftop_truth_model_v01_mm.obj",
  mtl: "rooftop_truth_model_v01.mtl",
  manifest: "rooftop_truth_model_v01_manifest.json",
};

function sha256(data) {
  return createHash("sha256").update(data).digest("hex");
}

function installFileReaderPolyfill() {
  if (typeof globalThis.FileReader !== "undefined") {
    return;
  }
  globalThis.FileReader = class FileReader {
    result = null;
    error = null;
    onloadend = null;

    readAsArrayBuffer(blob) {
      blob.arrayBuffer()
        .then((result) => {
          this.result = result;
          this.onloadend?.();
        })
        .catch((error) => {
          this.error = error;
          this.onloadend?.();
        });
    }

    readAsDataURL(blob) {
      blob.arrayBuffer()
        .then((result) => {
          const type = blob.type || "application/octet-stream";
          this.result = `data:${type};base64,${Buffer.from(result).toString("base64")}`;
          this.onloadend?.();
        })
        .catch((error) => {
          this.error = error;
          this.onloadend?.();
        });
    }
  };
}

function materialText() {
  const lines = ["# Rooftop truth model v01 material library"];
  for (const [name, definition] of Object.entries(MATERIAL_DEFINITIONS)) {
    const red = ((definition.color >> 16) & 255) / 255;
    const green = ((definition.color >> 8) & 255) / 255;
    const blue = (definition.color & 255) / 255;
    lines.push(
      "",
      `newmtl ${name}`,
      `Kd ${red.toFixed(6)} ${green.toFixed(6)} ${blue.toFixed(6)}`,
      "Ka 0.000000 0.000000 0.000000",
      "Ks 0.050000 0.050000 0.050000",
      `d ${definition.opacity.toFixed(6)}`,
      "illum 2",
    );
  }
  return `${lines.join("\n")}\n`;
}

function modelBounds(model) {
  const bounded = model.objects.filter((item) => item.bounds_mm);
  return [
    Math.min(...bounded.map((item) => item.bounds_mm[0])),
    Math.min(...bounded.map((item) => item.bounds_mm[1])),
    Math.min(...bounded.map((item) => item.z_min_mm)),
    Math.max(...bounded.map((item) => item.bounds_mm[2])),
    Math.max(...bounded.map((item) => item.bounds_mm[3])),
    Math.max(...bounded.map((item) => item.z_max_mm)),
  ];
}

function objectManifestEntry(object) {
  return {
    id: object.id,
    label: object.label,
    layer: object.layer,
    kind: object.kind,
    status: object.status,
    bounds_mm: object.bounds_mm,
    z_min_mm: object.z_min_mm,
    z_max_mm: object.z_max_mm,
    dimensions_mm: object.dimensions_mm,
    source: object.source,
  };
}

export function parseGlbJson(buffer) {
  if (buffer.length < 20
    || buffer.readUInt32LE(0) !== 0x46546c67
    || buffer.readUInt32LE(4) !== 2
    || buffer.readUInt32LE(8) !== buffer.length
    || buffer.readUInt32LE(16) !== 0x4e4f534a) {
    throw new Error("Invalid GLB header");
  }
  const jsonLength = buffer.readUInt32LE(12);
  if (jsonLength <= 0 || 20 + jsonLength > buffer.length) {
    throw new Error("Invalid GLB JSON chunk length");
  }
  return JSON.parse(buffer.subarray(20, 20 + jsonLength).toString("utf8").trimEnd());
}

export async function exportUniversalPackage(model, outDir, { sourcePath = SOURCE_PATH } = {}) {
  const validationErrors = validateModel(model);
  if (validationErrors.length > 0) {
    throw new Error(`Model validation failed:\n${validationErrors.join("\n")}`);
  }
  await mkdir(outDir, { recursive: true });
  installFileReaderPolyfill();

  const sceneMetres = createThreeScene(model, { units: "metres" });
  const glbArrayBuffer = await new GLTFExporter().parseAsync(sceneMetres, {
    binary: true,
    onlyVisible: false,
  });
  const glb = Buffer.from(glbArrayBuffer);

  const sceneMillimetres = createThreeScene(model, { units: "millimetres" });
  sceneMillimetres.traverse((object) => {
    object.visible = true;
  });
  sceneMillimetres.updateMatrixWorld(true);
  const rawObj = new OBJExporter().parse(sceneMillimetres);
  const obj = [
    "# Rooftop truth model v01",
    "# units: millimetres; up axis: Y",
    `mtllib ${FILENAMES.mtl}`,
    rawObj.replace(/^o /gm, "g ").trimEnd(),
    "",
  ].join("\n");
  const mtl = materialText();

  const glbPath = join(outDir, FILENAMES.glb);
  const objPath = join(outDir, FILENAMES.obj);
  const mtlPath = join(outDir, FILENAMES.mtl);
  const manifestPath = join(outDir, FILENAMES.manifest);
  await Promise.all([
    writeFile(glbPath, glb),
    writeFile(objPath, obj, "utf8"),
    writeFile(mtlPath, mtl, "utf8"),
  ]);

  const [sourceBytes, glbBytes, objBytes, mtlBytes] = await Promise.all([
    readFile(sourcePath),
    readFile(glbPath),
    readFile(objPath),
    readFile(mtlPath),
  ]);
  const manifest = {
    version: "rooftop-universal-3d-package-v01",
    model_version: model.version,
    source_version: model.source_version,
    candidate_status: model.candidate_status,
    source: {
      path: sourcePath,
      filename: basename(sourcePath),
      sha256: sha256(sourceBytes),
    },
    coordinate_system: {
      source_units: "millimetres",
      glb_units: "metres",
      obj_units: "millimetres",
      up_axis: "Y",
      mapping: "world X=local X; world Y=local Z; world Z=local Y",
      construction_setting_out: false,
    },
    model_bounds_mm: modelBounds(model),
    object_count: model.objects.length,
    layers: model.layers,
    objects: model.objects.map(objectManifestEntry),
    design_clashes: model.clashes,
    excluded_scope: model.excluded_scope,
    unhandled_source_objects: model.unhandled_source_objects,
    files: {
      glb: { filename: FILENAMES.glb, bytes: glbBytes.length, sha256: sha256(glbBytes) },
      obj: { filename: FILENAMES.obj, bytes: objBytes.length, sha256: sha256(objBytes) },
      mtl: { filename: FILENAMES.mtl, bytes: mtlBytes.length, sha256: sha256(mtlBytes) },
    },
  };
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

  return { glbPath, objPath, mtlPath, manifestPath, manifest };
}
