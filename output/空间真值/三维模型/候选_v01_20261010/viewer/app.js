import * as THREE from "./vendor/three.module.js";
import { OrbitControls } from "./vendor/OrbitControls.js";
import { GLTFLoader } from "./vendor/GLTFLoader.js";
import { fitDistanceForBounds } from "./camera.mjs";
import { setLayerVisibility } from "./layers.mjs";

const MODEL_VERSION = document.documentElement.dataset.modelVersion || "v02";
const MODEL_URL = `../rooftop_truth_model_${MODEL_VERSION}.glb`;
const LAYER_LABELS = {
  existing_floor_shell: "地面边界",
  existing_core_walls: "核心筒占位",
  existing_steel_columns: "钢柱 C1-C4",
  existing_roof_truss: "钢屋架（待复尺）",
  approved_fixed_design: "固定墙体与吧台",
  design_ceiling: "两级天花",
  future_glass_system: "未来玻璃系统",
};
const STATUS_LABELS = {
  verified: "已核验",
  owner_confirmed: "业主确认",
  derived: "推导占位",
  requires_site_measurement: "需现场复尺",
  user_decision_required: "待业主决策",
  owner_confirmed_resolved: "业主确认并解决",
};
const VIEW_LABELS = {
  plan: "俯视",
  isometric: "轴测",
  "V01-R1": "V01-R1",
  "V02-R1": "V02-R1",
  ceiling: "封顶核验",
};

const app = document.querySelector("#app");
const viewport = document.querySelector("#viewport");
const loadStatus = document.querySelector("#load-status");
const layerList = document.querySelector("#layer-list");
const layerCount = document.querySelector("#layer-count");
const objectDetails = document.querySelector("#object-details");
const selectionStatus = document.querySelector("#selection-status");
const cameraLabel = document.querySelector("#camera-label");
const panelToggle = document.querySelector("#panel-toggle");
const fitButton = document.querySelector("#fit-button");
const resetButton = document.querySelector("#reset-button");
const viewButtons = [...document.querySelectorAll("[data-view]")];
const layerControls = new Map();

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
viewport.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xd9dfdc);
const perspectiveCamera = new THREE.PerspectiveCamera(48, 1, 0.05, 300);
const orthographicCamera = new THREE.OrthographicCamera(-20, 20, 20, -20, 0.05, 300);
let activeCamera = perspectiveCamera;
let controls = createControls(activeCamera);
let modelRoot = null;
let modelBounds = new THREE.Box3();
let modelCenter = new THREE.Vector3();
let modelSize = new THREE.Vector3(1, 1, 1);
let currentView = "isometric";
let selectionHelper = null;

scene.add(new THREE.HemisphereLight(0xf7f6ef, 0x68706c, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
keyLight.position.set(22, 32, 18);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xd9e8e3, 1.1);
fillLight.position.set(-18, 12, -15);
scene.add(fillLight);

function createControls(camera) {
  const next = new OrbitControls(camera, renderer.domElement);
  next.enableDamping = true;
  next.dampingFactor = 0.08;
  next.screenSpacePanning = true;
  next.minDistance = 0.35;
  next.maxDistance = 130;
  next.maxPolarAngle = Math.PI * 0.495;
  return next;
}

function switchCamera(camera) {
  if (activeCamera === camera) {
    return;
  }
  const target = controls.target.clone();
  controls.dispose();
  activeCamera = camera;
  controls = createControls(activeCamera);
  controls.target.copy(target);
}

function viewportAspect() {
  return Math.max(viewport.clientWidth, 1) / Math.max(viewport.clientHeight, 1);
}

function setOrthographicFrustum() {
  const aspect = viewportAspect();
  const halfWidth = Math.max(modelSize.x * 0.62, modelSize.z * aspect * 0.62, 4);
  const halfHeight = halfWidth / aspect;
  orthographicCamera.left = -halfWidth;
  orthographicCamera.right = halfWidth;
  orthographicCamera.top = halfHeight;
  orthographicCamera.bottom = -halfHeight;
  orthographicCamera.updateProjectionMatrix();
}

function setPerspectivePose(position, target, fov = 48) {
  switchCamera(perspectiveCamera);
  perspectiveCamera.fov = fov;
  perspectiveCamera.position.fromArray(position);
  perspectiveCamera.up.set(0, 1, 0);
  perspectiveCamera.updateProjectionMatrix();
  controls.target.fromArray(target);
  controls.update();
}

function setCeilingPose() {
  const ceilingLayer = layerControls.get("design_ceiling")?.layer;
  if (!ceilingLayer) {
    return;
  }
  const ceilingBounds = new THREE.Box3().setFromObject(ceilingLayer);
  const ceilingSize = ceilingBounds.getSize(new THREE.Vector3());
  ceilingSize.y = Math.max(ceilingSize.y, modelSize.y, 1);
  const target = ceilingBounds.getCenter(new THREE.Vector3());
  target.y = Math.min(target.y, modelCenter.y * 0.9);
  const direction = new THREE.Vector3(1, 1.29, 0.94).normalize();
  const distance = fitDistanceForBounds(ceilingSize, 42, viewportAspect(), 1.16);
  const position = target.clone().addScaledVector(direction, distance);
  setPerspectivePose(position.toArray(), target.toArray(), 42);
}

function styleCeilingLayer() {
  const ceilingLayer = modelRoot.getObjectByName("design_ceiling");
  ceilingLayer?.traverse((object) => {
    if (!object.isMesh) {
      return;
    }
    const material = object.material.clone();
    material.color.set(0xb8ada0);
    material.opacity = 0.62;
    material.transparent = true;
    material.depthWrite = false;
    material.needsUpdate = true;
    object.material = material;
  });
}

function applyPreset(name) {
  if (!modelRoot) {
    return;
  }
  currentView = name;
  setLayerChecked("design_ceiling", name === "ceiling");
  if (name === "plan") {
    switchCamera(orthographicCamera);
    setOrthographicFrustum();
    orthographicCamera.position.set(modelCenter.x, Math.max(modelSize.x, modelSize.z) * 1.8, modelCenter.z);
    orthographicCamera.up.set(0, 0, -1);
    controls.target.copy(modelCenter);
    controls.update();
  } else if (name === "V01-R1") {
    setPerspectivePose([34.15, 1.62, 3.64], [23.8, 1.35, 3.75], 56);
  } else if (name === "V02-R1") {
    setPerspectivePose([24.6, 1.62, 3.05], [35.55, 1.2, 3.68], 55);
  } else if (name === "ceiling") {
    setCeilingPose();
  } else {
    const target = new THREE.Vector3(modelCenter.x, modelCenter.y * 0.45, modelCenter.z);
    const direction = new THREE.Vector3(1, 0.72, 0.85).normalize();
    const distance = fitDistanceForBounds(modelSize, 46, viewportAspect());
    const position = target.clone().addScaledVector(direction, distance);
    setPerspectivePose(
      position.toArray(),
      target.toArray(),
      46,
    );
  }
  cameraLabel.textContent = VIEW_LABELS[name];
  for (const button of viewButtons) {
    button.classList.toggle("is-active", button.dataset.view === name);
  }
}

function fitModel() {
  applyPreset("isometric");
}

function updateLayerCount() {
  const checkboxes = [...layerList.querySelectorAll("input[type='checkbox']")];
  layerCount.textContent = `${checkboxes.filter((item) => item.checked).length} / ${checkboxes.length}`;
}

function setLayerChecked(layerId, checked) {
  const control = layerControls.get(layerId);
  if (!control) {
    return;
  }
  control.checkbox.checked = checked;
  control.row.dataset.visible = String(checked);
  setLayerVisibility(control.layer, checked);
  updateLayerCount();
}

function buildLayerControls() {
  const fragment = document.createDocumentFragment();
  const layers = [];
  modelRoot.traverse((object) => {
    if (object.userData.layer === object.name && Object.hasOwn(LAYER_LABELS, object.name)) {
      layers.push(object);
    }
  });
  for (const layer of layers) {
    const row = document.createElement("label");
    row.className = "layer-row";
    row.dataset.status = layer.userData.status || "";
    row.dataset.layerId = layer.name;
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = layer.userData.default_visible !== false;
    layerControls.set(layer.name, { layer, checkbox, row });
    setLayerVisibility(layer, checkbox.checked);
    row.dataset.visible = String(checkbox.checked);
    checkbox.addEventListener("change", () => {
      setLayerChecked(layer.name, checkbox.checked);
    });
    const name = document.createElement("span");
    name.textContent = LAYER_LABELS[layer.name] || layer.name;
    const count = document.createElement("em");
    const objectCount = Array.isArray(layer.userData.object_ids) ? layer.userData.object_ids.length : layer.children.length;
    count.textContent = layer.userData.status === "requires_site_measurement" ? "待复尺" : String(objectCount);
    row.append(checkbox, name, count);
    fragment.append(row);
  }
  layerList.replaceChildren(fragment);
  updateLayerCount();
}

function addDetailRow(list, term, value, status = "") {
  const dt = document.createElement("dt");
  dt.textContent = term;
  const dd = document.createElement("dd");
  dd.textContent = value || "-";
  if (status) {
    dd.className = "status-value";
    dd.dataset.status = status;
  }
  list.append(dt, dd);
}

function showObjectDetails(object) {
  const data = object.userData;
  const title = document.createElement("p");
  title.className = "object-name";
  title.textContent = data.label || object.name;
  const list = document.createElement("dl");
  list.className = "detail-grid";
  const dimensions = Array.isArray(data.dimensions_mm)
    ? data.dimensions_mm.map((value) => `${value}`).join(" × ") + " mm"
    : "-";
  addDetailRow(list, "编号", data.id || object.name);
  addDetailRow(list, "尺寸", dimensions);
  addDetailRow(list, "状态", STATUS_LABELS[data.status] || data.status, data.status);
  if (data.plan_offset_status) {
    addDetailRow(
      list,
      "平面定位",
      STATUS_LABELS[data.plan_offset_status] || data.plan_offset_status,
      data.plan_offset_status,
    );
  }
  addDetailRow(list, "图层", LAYER_LABELS[data.layer] || data.layer);
  addDetailRow(list, "依据", data.source);
  objectDetails.replaceChildren(title, list);
  selectionStatus.textContent = "已选择";

  if (selectionHelper) {
    scene.remove(selectionHelper);
    selectionHelper.geometry.dispose();
    selectionHelper.material.dispose();
  }
  selectionHelper = new THREE.BoxHelper(object, 0x9b5f4c);
  selectionHelper.material.depthTest = false;
  selectionHelper.renderOrder = 10;
  scene.add(selectionHelper);
}

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerDown = null;

function isObjectVisibleInHierarchy(object) {
  let current = object;
  while (current) {
    if (!current.visible) {
      return false;
    }
    if (current === modelRoot) {
      return true;
    }
    current = current.parent;
  }
  return false;
}

renderer.domElement.addEventListener("pointerdown", (event) => {
  pointerDown = [event.clientX, event.clientY];
});
renderer.domElement.addEventListener("pointerup", (event) => {
  if (!modelRoot || !pointerDown || Math.hypot(event.clientX - pointerDown[0], event.clientY - pointerDown[1]) > 5) {
    return;
  }
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, activeCamera);
  const hit = raycaster.intersectObject(modelRoot, true).find(
    (item) => item.object.userData.id && isObjectVisibleInHierarchy(item.object),
  );
  if (hit) {
    showObjectDetails(hit.object);
  }
});

for (const button of viewButtons) {
  button.addEventListener("click", () => applyPreset(button.dataset.view));
}

panelToggle.addEventListener("click", () => {
  const collapsed = app.classList.toggle("panel-collapsed");
  panelToggle.setAttribute("aria-expanded", String(!collapsed));
  requestAnimationFrame(resize);
});
fitButton.addEventListener("click", fitModel);
resetButton.addEventListener("click", () => applyPreset(currentView));

function resize() {
  const width = Math.max(viewport.clientWidth, 1);
  const height = Math.max(viewport.clientHeight, 1);
  renderer.setSize(width, height, false);
  perspectiveCamera.aspect = width / height;
  perspectiveCamera.updateProjectionMatrix();
  setOrthographicFrustum();
  if (currentView === "ceiling" && modelRoot) {
    setCeilingPose();
  }
}

window.addEventListener("resize", resize);
if (window.matchMedia("(max-width: 720px)").matches) {
  app.classList.add("panel-collapsed");
  panelToggle.setAttribute("aria-expanded", "false");
}

new GLTFLoader().load(
  MODEL_URL,
  (gltf) => {
    modelRoot = gltf.scene;
    scene.add(modelRoot);
    styleCeilingLayer();
    modelBounds.setFromObject(modelRoot);
    modelBounds.getCenter(modelCenter);
    modelBounds.getSize(modelSize);

    const grid = new THREE.GridHelper(48, 48, 0x87918b, 0xbfc6c1);
    grid.name = "display_grid";
    grid.position.set(modelCenter.x, -0.008, modelCenter.z);
    grid.material.opacity = 0.34;
    grid.material.transparent = true;
    scene.add(grid);

    buildLayerControls();
    resize();
    applyPreset("isometric");
    loadStatus.textContent = "已载入";
    loadStatus.classList.add("is-ready");
    document.documentElement.dataset.viewerReady = "true";
    window.__rooftopViewerReady = true;
    window.__rooftopViewer = {
      applyPreset,
      cameras: { perspectiveCamera, orthographicCamera },
      get activeCamera() { return activeCamera; },
      get currentView() { return currentView; },
      get modelRoot() { return modelRoot; },
      renderer,
      scene,
    };
    window.dispatchEvent(new CustomEvent("rooftop-viewer-ready"));
  },
  undefined,
  (error) => {
    console.error(error);
    loadStatus.textContent = "模型读取失败";
    loadStatus.classList.add("is-error");
    document.documentElement.dataset.viewerError = String(error);
    window.__rooftopViewerError = String(error);
  },
);

function animate() {
  controls.update();
  if (selectionHelper) {
    selectionHelper.update();
  }
  renderer.render(scene, activeCamera);
  requestAnimationFrame(animate);
}

resize();
animate();
