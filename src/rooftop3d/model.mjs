import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

export const ROOT = fileURLToPath(new URL("../..", import.meta.url));
export const V04_SOURCE_PATH = resolve(
  ROOT,
  "output/空间真值/整层灰模/候选_v04_20261010/楼顶整层灰模_v04_坐标场景.json",
);
export const V05_SOURCE_PATH = resolve(
  ROOT,
  "output/空间真值/整层灰模/候选_v05_20261011/楼顶整层灰模_v05_坐标场景.json",
);
export const SOURCE_PATH = V05_SOURCE_PATH;

const MODEL_VERSION_BY_SOURCE = new Map([
  ["rooftop-whole-floor-truth-model-v04", "rooftop-universal-3d-model-v01"],
  ["rooftop-whole-floor-truth-model-v05", "rooftop-universal-3d-model-v02"],
]);

export function loadTruthScene(path = SOURCE_PATH) {
  const source = JSON.parse(readFileSync(path, "utf8"));
  if (!MODEL_VERSION_BY_SOURCE.has(source.version)) {
    throw new Error(`Unsupported rooftop truth scene version: ${source.version}`);
  }
  return source;
}

function descriptorFromSource(sourceObject, kind, overrides = {}) {
  const zMin = overrides.z_min_mm ?? sourceObject.z_mm ?? sourceObject.level_mm ?? 0;
  const height = overrides.height_mm ?? sourceObject.height_mm ?? 0;
  return {
    id: sourceObject.id,
    label: sourceObject.label,
    layer: sourceObject.layer,
    kind,
    bounds_mm: sourceObject.bounds_mm ? [...sourceObject.bounds_mm] : null,
    z_min_mm: zMin,
    z_max_mm: zMin + height,
    height_mm: height,
    dimensions_mm: sourceObject.dimensions_mm ? [...sourceObject.dimensions_mm] : null,
    status: sourceObject.status,
    source: sourceObject.source,
    default_visible: sourceObject.display !== false,
    metadata: Object.fromEntries(
      Object.entries(sourceObject).filter(([key]) => ![
        "id",
        "label",
        "layer",
        "category",
        "bounds_mm",
        "height_mm",
        "z_mm",
        "dimensions_mm",
        "status",
        "source",
        "display",
      ].includes(key)),
    ),
    ...overrides,
  };
}

function makeEquipment(source, run, rack) {
  const labels = {
    stainless_counter_fridge_1: "1号不锈钢操作台冰柜",
    stainless_counter_fridge_2_with_electric_stove: "2号不锈钢操作台冰柜（带电灶）",
    stainless_blank_worktop: "500空置操作台",
    stainless_sink_with_glass_rinser: "洗菜池（带高压洗杯器）",
    stacked_appliance_rack: "上下叠放设备架",
  };
  let cursorY = run.bounds_mm[1];

  return source.equipment_sequence.map((item) => {
    const isRack = item.id === "E5";
    const depth = isRack ? rack.bounds_mm[2] - rack.bounds_mm[0] : run.bounds_mm[2] - run.bounds_mm[0];
    const x2 = run.bounds_mm[2];
    const y1 = cursorY;
    const y2 = y1 + item.length_mm;
    const height = isRack ? rack.height_mm : run.height_mm;
    cursorY = y2;

    return {
      id: item.id,
      label: labels[item.type] ?? item.type,
      layer: run.layer,
      kind: "fixed_fixture",
      bounds_mm: [x2 - depth, y1, x2, y2],
      z_min_mm: 0,
      z_max_mm: height,
      height_mm: height,
      length_mm: item.length_mm,
      dimensions_mm: [depth, item.length_mm, height],
      status: "owner_confirmed",
      source: `${run.source}; subdivided by equipment_sequence ${item.id}`,
      default_visible: true,
      metadata: { equipment_type: item.type },
    };
  });
}

function buildLayerMap(source, objects) {
  const sourceLayers = new Map(source.layers.map((layer) => [layer.id, layer]));
  const layerIds = [
    "existing_floor_shell",
    "existing_core_walls",
    "existing_steel_columns",
    "existing_roof_truss",
    "approved_fixed_design",
    "design_ceiling",
    "future_glass_system",
  ];

  return Object.fromEntries(layerIds.map((id) => {
    const sourceLayer = sourceLayers.get(id);
    const requiresMeasurement = id === "existing_roof_truss" || id === "future_glass_system";
    return [id, {
      default_visible: sourceLayer?.default_visible ?? false,
      object_ids: objects.filter((item) => item.layer === id).map((item) => item.id),
      ...(requiresMeasurement ? { status: "requires_site_measurement" } : {}),
    }];
  }));
}

export function buildModelDescriptors(source) {
  if (!MODEL_VERSION_BY_SOURCE.has(source.version)) {
    throw new Error(`Unsupported rooftop truth scene version: ${source.version}`);
  }

  const sourceById = new Map(source.objects.map((item) => [item.id, item]));
  const handled = new Set();
  const objects = [];
  const kindByCategory = {
    floor: "floor_plane",
    room_volume: "room_volume",
    steel_column: "steel_column",
    wall: "wall",
    fixed_design_zone: "control_area",
    opening_control: "control_line",
    opening: "opening_void",
    ceiling_control: "ceiling_plane",
  };

  for (const sourceObject of source.objects) {
    if (["bar_body", "bar_flip_gate", "equipment_run", "equipment_rack"].includes(sourceObject.id)) {
      continue;
    }
    const kind = kindByCategory[sourceObject.category];
    if (!kind) {
      continue;
    }
    const overrides = kind === "ceiling_plane"
      ? {
          z_min_mm: sourceObject.height_mm,
          z_max_mm: sourceObject.height_mm,
          height_mm: 0,
          default_visible: false,
        }
      : {};
    objects.push(descriptorFromSource(sourceObject, kind, overrides));
    handled.add(sourceObject.id);
  }

  const sourceBar = sourceById.get("bar_body");
  const sourceGate = sourceById.get("bar_flip_gate");
  const [barX1, barY1, barX2, barY2] = sourceBar.bounds_mm;
  const gateLength = sourceGate.bounds_mm[3] - sourceGate.bounds_mm[1];
  objects.push(descriptorFromSource(sourceGate, "fixed_fixture", {
    bounds_mm: [barX1, barY1, barX2, barY1 + gateLength],
    dimensions_mm: [barX2 - barX1, gateLength, sourceBar.height_mm],
    height_mm: sourceBar.height_mm,
    z_min_mm: 0,
    z_max_mm: sourceBar.height_mm,
  }));
  objects.push(descriptorFromSource(sourceBar, "fixed_fixture", {
    id: "bar_body_fixed_run",
    label: "吧台固定段4230×800×1000",
    bounds_mm: [barX1, barY1 + gateLength, barX2, barY2],
    dimensions_mm: [barX2 - barX1, barY2 - barY1 - gateLength, sourceBar.height_mm],
    z_min_mm: 0,
    z_max_mm: sourceBar.height_mm,
  }));
  handled.add("bar_body");
  handled.add("bar_flip_gate");

  const equipment = makeEquipment(
    source,
    sourceById.get("equipment_run"),
    sourceById.get("equipment_rack"),
  );
  objects.push(...equipment);
  handled.add("equipment_run");
  handled.add("equipment_rack");

  const layers = buildLayerMap(source, objects);
  const clashes = (source.design_clashes ?? []).map((clash) => ({
    id: clash.id,
    window_head_mm: clash.window_head_mm,
    ceiling_height_mm: clash.level_1_ceiling_mm,
    overlap_mm: clash.level_1_overlap_mm,
    status: clash.status,
    model_action: clash.model_action,
    note: clash.note,
  }));
  const resolvedDesignDecisions = structuredClone(source.resolved_design_decisions ?? []);

  return {
    version: MODEL_VERSION_BY_SOURCE.get(source.version),
    source_version: source.version,
    candidate_status: source.candidate_status,
    units: "millimetres",
    topology: structuredClone(source.tea_room_topology),
    coordinate_system: structuredClone(source.coordinate_system),
    layers,
    objects,
    equipment,
    clashes,
    resolved_design_decisions: resolvedDesignDecisions,
    excluded_scope: [...source.excluded_scope],
    unhandled_source_objects: source.objects
      .filter((item) => !handled.has(item.id))
      .map((item) => item.id),
  };
}

function boxesOverlap(a, b) {
  return a[0] < b[2] && a[2] > b[0] && a[1] < b[3] && a[3] > b[1];
}

function vectorsAreParallel(a, b) {
  return a[0] * b[1] - a[1] * b[0] === 0;
}

export function validateModel(model) {
  const errors = [];
  const points = model.topology.points_mm;
  const [a, c, b, d, e] = ["A", "C", "B", "D", "E"].map((id) => points[id]);
  const topologyPoints = [a, c, b, d, e];
  const topologyFinite = topologyPoints.every((point) =>
    Array.isArray(point) && point.length === 2 && point.every(Number.isFinite));
  const ac = topologyFinite ? [c[0] - a[0], c[1] - a[1]] : [Number.NaN, Number.NaN];
  const ab = topologyFinite ? [b[0] - a[0], b[1] - a[1]] : [Number.NaN, Number.NaN];
  if (!topologyFinite || !vectorsAreParallel(ac, ab)) {
    errors.push("A/C/B must be finite and collinear");
  }
  if (topologyFinite) {
    const ce = [e[0] - c[0], e[1] - c[1]];
    const bd = [d[0] - b[0], d[1] - b[1]];
    if (!vectorsAreParallel(ce, bd)) {
      errors.push("C-E and B-D must be parallel");
    }
    if (b[0] - c[0] !== 3200 || d[1] - b[1] !== 4100) {
      errors.push("tea room must be 3200x4100 mm");
    }
  }

  const byId = new Map(model.objects.map((item) => [item.id, item]));
  for (const object of model.objects) {
    if (!object.bounds_mm) {
      continue;
    }
    if (!object.bounds_mm.every(Number.isFinite)) {
      errors.push(`${object.id} has non-finite bounds`);
      continue;
    }
    if (object.bounds_mm[2] <= object.bounds_mm[0] || object.bounds_mm[3] <= object.bounds_mm[1]) {
      errors.push(`${object.id} has non-positive plan dimensions`);
    }
    if (![object.z_min_mm, object.z_max_mm].every(Number.isFinite) || object.z_max_mm < object.z_min_mm) {
      errors.push(`${object.id} has invalid vertical bounds`);
    }
  }

  if (model.objects.filter((item) => item.kind === "steel_column").length !== 4) {
    errors.push("model must contain exactly four steel columns");
  }
  const gate = byId.get("bar_flip_gate");
  const fixedBar = byId.get("bar_body_fixed_run");
  if (!gate || !fixedBar || boxesOverlap(gate.bounds_mm, fixedBar.bounds_mm)) {
    errors.push("bar flip gate and fixed run must exist without overlap");
  }

  const equipmentLength = model.equipment.reduce((sum, item) => sum + item.length_mm, 0);
  if (equipmentLength !== 4400) {
    errors.push("equipment chain must total 4400 mm");
  }
  for (let index = 1; index < model.equipment.length; index += 1) {
    if (model.equipment[index - 1].bounds_mm[3] !== model.equipment[index].bounds_mm[1]) {
      errors.push("equipment chain must be contiguous");
      break;
    }
  }
  if (model.equipment[0]?.bounds_mm[1] !== 1760 || model.equipment.at(-1)?.bounds_mm[3] !== 6160) {
    errors.push("equipment chain must close from Y=1760 to Y=6160");
  }
  if (model.objects.filter((item) => item.kind === "opening_void" && item.id === "tea_room_only_window").length !== 1) {
    errors.push("model must preserve exactly one tea-room window void");
  }

  const terraceWall = byId.get("tea_terrace_boundary_wall");
  if (topologyFinite && (!terraceWall
    || e[1] !== d[1]
    || terraceWall.bounds_mm[0] !== e[0]
    || terraceWall.bounds_mm[2] !== d[0]
    || terraceWall.bounds_mm[3] !== e[1])) {
    errors.push("E-D must coincide with the terrace boundary wall");
  }
  if (model.version === "rooftop-universal-3d-model-v01") {
    const clash = model.clashes.find((item) => item.id === "tea_window_head_vs_ceiling");
    if (!clash || clash.overlap_mm !== 300 || clash.status !== "user_decision_required") {
      errors.push("v01 window-head ceiling clash must remain visible at 300 mm");
    }
  } else if (model.version === "rooftop-universal-3d-model-v02") {
    const window = byId.get("tea_room_only_window");
    const headWall = byId.get("tea_window_head_wall");
    if (!window
      || window.z_min_mm !== 350
      || window.z_max_mm !== 2450
      || window.height_mm !== 2100
      || window.dimensions_mm?.[0] !== 3220
      || window.dimensions_mm?.[1] !== 2100) {
      errors.push("v02 tea-room window must be 3220x2100 mm from Z=350 to Z=2450");
    }
    if (!headWall || headWall.z_min_mm !== 2450 || headWall.z_max_mm !== 3020) {
      errors.push("v02 upper infill wall must close from Z=2450 to Z=3020");
    }
    if (model.clashes.length !== 0) {
      errors.push("v02 must not retain an unresolved window-head ceiling clash");
    }
    const resolution = model.resolved_design_decisions.find(
      (item) => item.id === "tea_window_head_vs_ceiling",
    );
    if (!resolution
      || resolution.status !== "owner_confirmed_resolved"
      || resolution.former_overlap_mm !== 300
      || resolution.new_window_head_mm !== 2450) {
      errors.push("v02 must retain the owner-confirmed window-head resolution record");
    }
  }
  if (model.unhandled_source_objects.length > 0) {
    errors.push(`unhandled source objects: ${model.unhandled_source_objects.join(", ")}`);
  }

  return errors;
}
