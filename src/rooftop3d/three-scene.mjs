import * as THREE from "../../tools/rooftop3d-web/node_modules/three/build/three.module.js";

export const MATERIAL_DEFINITIONS = {
  floor_plane_verified: { color: 0xb8b3aa, opacity: 1 },
  floor_plane_derived: { color: 0xc9c3b8, opacity: 1 },
  floor_plane_owner_confirmed: { color: 0xb9b09f, opacity: 1 },
  room_volume_derived: { color: 0x7d8588, opacity: 0.92 },
  steel_column_owner_confirmed: { color: 0x4d5960, opacity: 1 },
  wall_verified: { color: 0xb79c7d, opacity: 1 },
  wall_owner_confirmed: { color: 0xcfbda7, opacity: 1 },
  wall_derived: { color: 0xc99972, opacity: 1 },
  fixed_fixture_owner_confirmed: { color: 0x895c42, opacity: 1 },
  control_area_owner_confirmed: { color: 0x4d8a83, opacity: 0.34 },
  control_line_owner_confirmed: { color: 0x208079, opacity: 1 },
  opening_void_owner_confirmed: { color: 0x208079, opacity: 1 },
  ceiling_plane_owner_confirmed: { color: 0xd8c990, opacity: 0.28 },
};

const MATERIAL_FALLBACK = { color: 0x9a8f82, opacity: 1 };

function materialNameFor(descriptor) {
  return `${descriptor.kind}_${descriptor.status}`;
}

function meshMaterialFor(descriptor, cache) {
  const name = materialNameFor(descriptor);
  if (!cache.has(name)) {
    const definition = MATERIAL_DEFINITIONS[name] ?? MATERIAL_FALLBACK;
    const material = new THREE.MeshStandardMaterial({
      color: definition.color,
      opacity: definition.opacity,
      transparent: definition.opacity < 1,
      side: THREE.DoubleSide,
      roughness: 0.82,
      metalness: descriptor.kind === "steel_column" ? 0.35 : 0.02,
    });
    material.name = name;
    cache.set(name, material);
  }
  return cache.get(name);
}

function helperMaterialFor(descriptor, cache) {
  const name = materialNameFor(descriptor);
  if (!cache.has(name)) {
    const definition = MATERIAL_DEFINITIONS[name] ?? MATERIAL_FALLBACK;
    const material = new THREE.MeshBasicMaterial({
      color: definition.color,
      opacity: definition.opacity,
      transparent: definition.opacity < 1,
      side: THREE.DoubleSide,
    });
    material.name = name;
    cache.set(name, material);
  }
  return cache.get(name);
}

function objectExtras(descriptor) {
  return {
    id: descriptor.id,
    label: descriptor.label,
    layer: descriptor.layer,
    kind: descriptor.kind,
    status: descriptor.status,
    source: descriptor.source,
    bounds_mm: descriptor.bounds_mm,
    dimensions_mm: descriptor.dimensions_mm,
    height_mm: descriptor.height_mm,
    z_min_mm: descriptor.z_min_mm,
    z_max_mm: descriptor.z_max_mm,
    default_visible: descriptor.default_visible,
    ...descriptor.metadata,
  };
}

function createBox(descriptor, scale, cache) {
  const [x1, y1, x2, y2] = descriptor.bounds_mm;
  const width = (x2 - x1) * scale;
  const depth = (y2 - y1) * scale;
  const height = (descriptor.z_max_mm - descriptor.z_min_mm) * scale;
  const geometry = new THREE.BoxGeometry(width, height, depth);
  const mesh = new THREE.Mesh(geometry, meshMaterialFor(descriptor, cache));
  mesh.position.set(
    ((x1 + x2) / 2) * scale,
    ((descriptor.z_min_mm + descriptor.z_max_mm) / 2) * scale,
    ((y1 + y2) / 2) * scale,
  );
  return mesh;
}

function createPlane(descriptor, scale, cache) {
  const [x1, y1, x2, y2] = descriptor.bounds_mm;
  const geometry = new THREE.PlaneGeometry((x2 - x1) * scale, (y2 - y1) * scale);
  geometry.rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(geometry, meshMaterialFor(descriptor, cache));
  mesh.position.set(
    ((x1 + x2) / 2) * scale,
    descriptor.z_min_mm * scale,
    ((y1 + y2) / 2) * scale,
  );
  return mesh;
}

function createControl(descriptor, scale, cache) {
  if (!descriptor.bounds_mm) {
    return new THREE.Object3D();
  }
  if (descriptor.kind === "control_area") {
    const plane = createPlane({ ...descriptor, z_min_mm: 8 }, scale, cache);
    plane.renderOrder = 2;
    return plane;
  }
  const [x1, y1, x2, y2] = descriptor.bounds_mm;
  const width = (x2 - x1) * scale;
  const depth = (y2 - y1) * scale;
  const inset = Math.min(width, depth) * 0.18;
  const shape = new THREE.Shape();
  shape.moveTo(-width / 2, -depth / 2);
  shape.lineTo(width / 2, -depth / 2);
  shape.lineTo(width / 2, depth / 2);
  shape.lineTo(-width / 2, depth / 2);
  shape.closePath();
  if (width > inset * 2 && depth > inset * 2) {
    const hole = new THREE.Path();
    hole.moveTo(-width / 2 + inset, -depth / 2 + inset);
    hole.lineTo(-width / 2 + inset, depth / 2 - inset);
    hole.lineTo(width / 2 - inset, depth / 2 - inset);
    hole.lineTo(width / 2 - inset, -depth / 2 + inset);
    hole.closePath();
    shape.holes.push(hole);
  }
  const geometry = new THREE.ShapeGeometry(shape);
  geometry.rotateX(-Math.PI / 2);
  const helper = new THREE.Mesh(geometry, helperMaterialFor(descriptor, cache));
  helper.position.set(((x1 + x2) / 2) * scale, 18 * scale, ((y1 + y2) / 2) * scale);
  helper.renderOrder = 3;
  return helper;
}

function createSceneObject(descriptor, scale, cache) {
  if (["floor_plane", "ceiling_plane"].includes(descriptor.kind)) {
    return createPlane(descriptor, scale, cache);
  }
  if (["control_area", "control_line"].includes(descriptor.kind)) {
    return createControl(descriptor, scale, cache);
  }
  if (descriptor.kind === "opening_void") {
    return new THREE.Object3D();
  }
  return createBox(descriptor, scale, cache);
}

export function createThreeScene(model, { units = "metres" } = {}) {
  if (!new Set(["metres", "millimetres"]).has(units)) {
    throw new Error(`Unsupported scene units: ${units}`);
  }
  const scale = units === "metres" ? 0.001 : 1;
  const scene = new THREE.Scene();
  const versionSuffix = model.version.match(/-(v\d+)$/)?.[1] ?? "unversioned";
  scene.name = `rooftop_truth_model_${versionSuffix}`;
  scene.userData = {
    version: model.version,
    candidate_status: model.candidate_status,
    units,
    up_axis: "Y",
    axis_mapping: "world X=local X; world Y=local Z; world Z=local Y",
    clashes: model.clashes,
    resolved_design_decisions: model.resolved_design_decisions,
  };
  const materialCache = new Map();

  for (const [layerId, layer] of Object.entries(model.layers)) {
    const group = new THREE.Group();
    group.name = layerId;
    group.visible = layer.default_visible;
    group.userData = {
      layer: layerId,
      default_visible: layer.default_visible,
      status: layer.status ?? null,
      object_ids: layer.object_ids,
    };
    scene.add(group);
  }

  for (const descriptor of model.objects) {
    const object = createSceneObject(descriptor, scale, materialCache);
    object.name = descriptor.id;
    object.visible = descriptor.default_visible;
    object.userData = objectExtras(descriptor);
    scene.getObjectByName(descriptor.layer).add(object);
  }
  scene.updateMatrixWorld(true);
  return scene;
}
