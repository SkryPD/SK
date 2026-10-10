# Rooftop Universal 3D Truth Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本项目 `AGENTS.md` 禁止子智能体，全部任务必须在当前线程内顺序执行。

**Goal:** 从已确认的 v04 空间真值 JSON 生成可追溯的 GLB、OBJ/MTL、manifest 和本地 Three.js 查看器，并完成自动与视觉核验。

**Architecture:** 先把 v04 对象转换为毫米制中间模型描述，再由同一描述构造米制 GLB 和毫米制 OBJ，避免格式漂移。查看器读取 GLB 节点 extras 实现图层、对象信息和预设机位；所有未知项保留证据状态，不生成假几何。

**Tech Stack:** Node.js 24、Three.js 0.186.1、Lucide Static 1.55.0、Node test runner、HTML/CSS/JavaScript、内置浏览器 Playwright。

---

### Task 1: 建立依赖与中间模型契约

**Files:**
- Create: `tools/rooftop3d-web/package.json`
- Create: `tools/rooftop3d-web/package-lock.json`
- Create: `tests/test_rooftop3d_scene.mjs`
- Create: `src/rooftop3d/model.mjs`
- Modify: `.gitignore`

- [ ] **Step 1: 写失败测试，锁定输入版本和关键几何**

测试必须导入 `loadTruthScene()` 与 `buildModelDescriptors()`，并断言：

```js
assert.equal(source.version, 'rooftop-whole-floor-truth-model-v04');
assert.deepEqual(model.topology.points_mm.C, [34240, 6160]);
assert.deepEqual(byId.get('tea_room_floor').bounds_mm, [34240, 6160, 37440, 10260]);
assert.equal(model.objects.filter((item) => item.kind === 'steel_column').length, 4);
assert.deepEqual(byId.get('bar_flip_gate').bounds_mm, [35040, 1130, 35840, 1930]);
assert.deepEqual(byId.get('bar_body_fixed_run').bounds_mm, [35040, 1930, 35840, 6160]);
assert.equal(model.equipment.reduce((sum, item) => sum + item.length_mm, 0), 4400);
assert.deepEqual(model.layers.existing_roof_truss, { default_visible: false, object_ids: [], status: 'requires_site_measurement' });
assert.deepEqual(model.layers.future_glass_system, { default_visible: false, object_ids: [], status: 'requires_site_measurement' });
assert.equal(model.clashes[0].id, 'tea_window_head_vs_ceiling');
assert.equal(model.clashes[0].overlap_mm, 300);
assert.deepEqual(validateModel(model), []);
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `node --test tests/test_rooftop3d_scene.mjs`

Expected: FAIL，提示 `src/rooftop3d/model.mjs` 不存在。

- [ ] **Step 3: 安装固定版本依赖**

Run: `npm install --prefix tools/rooftop3d-web --save-exact three@0.186.1 lucide-static@1.55.0`

Expected: 生成独立 `package.json` 与 lockfile；不安装全局包。

- [ ] **Step 4: 实现毫米制中间模型**

`model.mjs` 的公共接口必须固定为：

```js
export const ROOT = fileURLToPath(new URL('../..', import.meta.url));
export const SOURCE_PATH = resolve(ROOT, 'output/空间真值/整层灰模/候选_v04_20261010/楼顶整层灰模_v04_坐标场景.json');
export function loadTruthScene(path = SOURCE_PATH);
export function buildModelDescriptors(source);
export function validateModel(model);
```

具体契约：

- `loadTruthScene()` 同步读取 UTF-8 JSON；版本不是 `rooftop-whole-floor-truth-model-v04` 时抛出包含实际版本的错误。
- `buildModelDescriptors()` 只读取源对象和明确规则：地坪为 `plane`；墙、柱、核心筒和固定构件为 `box`；开放通道为 `control_line`；吊顶为默认隐藏的 `plane`。
- 固定吧台由 `bar_flip_gate` 与 `bar_body_fixed_run` 两块互不重叠对象组成；不得再输出源 `bar_body` 总块。
- 设备从源 `equipment_run.bounds_mm[1]` 起按 E1-E5 的 `length_mm` 顺序闭合；E1-E4 使用600mm进深、900mm高度，E5复用已确认 `equipment_rack` 的800mm进深、1800mm高度；不得输出源 `equipment_run` 总块。
- `existing_roof_truss` 与 `future_glass_system` 始终建立为空图层，状态为 `requires_site_measurement`。
- `validateModel()` 返回错误字符串数组，逐项检查 A/C/B 共线、C-E 与 B-D 平行、E-D 与露台边界重合、有限且为正的实体尺寸、四柱数量、吧台不重叠、设备链4400mm闭合、茶室唯一窗以及300mm碰撞元数据；任何错误都会阻止导出。

- [ ] **Step 5: 运行测试确认 GREEN**

Run: `node --test tests/test_rooftop3d_scene.mjs`

Expected: PASS。

- [ ] **Step 6: 提交 Task 1**

```powershell
git add -- .gitignore tools/rooftop3d-web/package.json tools/rooftop3d-web/package-lock.json tests/test_rooftop3d_scene.mjs src/rooftop3d/model.mjs
git commit -m "feat: define rooftop 3d truth scene"
```

### Task 2: 导出 GLB、OBJ/MTL 与 manifest

**Files:**
- Create: `tests/test_rooftop3d_exports.mjs`
- Create: `src/rooftop3d/three-scene.mjs`
- Create: `src/rooftop3d/exporters.mjs`
- Create: `scripts/build_rooftop_universal_model_v01.mjs`
- Create: `output/空间真值/三维模型/候选_v01_20261010/rooftop_truth_model_v01.glb`
- Create: `output/空间真值/三维模型/候选_v01_20261010/rooftop_truth_model_v01_mm.obj`
- Create: `output/空间真值/三维模型/候选_v01_20261010/rooftop_truth_model_v01.mtl`
- Create: `output/空间真值/三维模型/候选_v01_20261010/rooftop_truth_model_v01_manifest.json`

- [ ] **Step 1: 写失败测试，锁定导出结构**

测试在临时目录调用 `exportUniversalPackage(model, outDir)`，检查：

```js
assert.equal(glb.readUInt32LE(0), 0x46546c67);
assert.equal(glb.readUInt32LE(4), 2);
assert.ok(glbJson.nodes.some((node) => node.name === 'tea_background_wall'));
assert.ok(objText.includes('g tea_background_wall'));
assert.ok(objText.includes('mtllib rooftop_truth_model_v01.mtl'));
assert.equal(manifest.coordinate_system.glb_units, 'metres');
assert.equal(manifest.coordinate_system.obj_units, 'millimetres');
assert.equal(manifest.candidate_status, 'candidate_requires_clash_decision');
assert.equal(manifest.design_clashes[0].overlap_mm, 300);
assert.deepEqual(manifest.layers.existing_roof_truss.object_ids, []);
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `node --test tests/test_rooftop3d_exports.mjs`

Expected: FAIL，提示导出模块不存在。

- [ ] **Step 3: 实现 Three.js 场景构造**

`createThreeScene(model, { units })` 必须统一执行轴映射：

```js
const scale = units === 'metres' ? 0.001 : 1;
const toWorld = ([x, y, z]) => [x * scale, z * scale, y * scale];
```

每个 mesh 的 `name` 使用稳定对象 ID，`userData` 写入 label、layer、status、source、bounds_mm 和 dimensions_mm。图层组使用原 layer ID；天花组默认隐藏但导出时设置 `onlyVisible:false`。

- [ ] **Step 4: 实现导出器**

- GLB 使用 `GLTFExporter.parseAsync(scene, { binary: true, onlyVisible: false })`。
- OBJ 使用 `OBJExporter.parse(sceneMm)`；导出前把所有图层临时设为可见。
- MTL 由稳定材料表生成，材质名与 OBJ `usemtl` 一致。
- manifest 记录源文件 SHA-256、模型边界、对象数量、全部图层（含两个空图层）、状态、300mm冲突和关键硬约束；未识别源对象写入 `unhandled_source_objects`，不得静默丢弃。

- [ ] **Step 5: 运行测试确认 GREEN**

Run: `node --test tests/test_rooftop3d_exports.mjs`

Expected: PASS，临时 GLB/OBJ/MTL 可解析。

- [ ] **Step 6: 生成候选模型包**

Run: `node scripts/build_rooftop_universal_model_v01.mjs`

Expected: 四个模型文件写入独立候选目录，旧输出未覆盖。

- [ ] **Step 7: 提交 Task 2**

```powershell
git add -- tests/test_rooftop3d_exports.mjs src/rooftop3d/three-scene.mjs src/rooftop3d/exporters.mjs scripts/build_rooftop_universal_model_v01.mjs output/空间真值/三维模型/候选_v01_20261010
git commit -m "feat: export rooftop glb and obj models"
```

### Task 3: 建立本地 Three.js 查看器

**Files:**
- Create: `tests/test_rooftop3d_viewer.mjs`
- Create: `src/rooftop3d/viewer/index.html`
- Create: `src/rooftop3d/viewer/styles.css`
- Create: `src/rooftop3d/viewer/app.js`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/three.module.js`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/OrbitControls.js`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/GLTFLoader.js`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/THREE-LICENSE.txt`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/icons/maximize.svg`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/icons/rotate-ccw.svg`
- Create: `output/空间真值/三维模型/候选_v01_20261010/viewer/vendor/icons/panel-left.svg`

- [ ] **Step 1: 写失败测试，锁定查看器功能和离线性**

测试必须检查：

```js
assert.ok(html.includes('id="viewport"'));
assert.ok(html.includes('id="layer-list"'));
assert.ok(app.includes('V01-R1'));
assert.ok(app.includes('V02-R1'));
assert.ok(!`${html}\n${app}`.match(/https?:\/\//));
assert.ok(existsSync(resolve(viewerDir, 'vendor/three.module.js')));
assert.ok(existsSync(resolve(viewerDir, 'vendor/GLTFLoader.js')));
assert.ok(existsSync(resolve(viewerDir, 'vendor/OrbitControls.js')));
assert.ok(existsSync(resolve(viewerDir, 'vendor/icons/maximize.svg')));
assert.ok(html.includes('aria-label="切换控制面板"'));
assert.ok(app.includes('design_ceiling'));
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `node --test tests/test_rooftop3d_viewer.mjs`

Expected: FAIL，查看器文件尚不存在。

- [ ] **Step 3: 实现查看器界面**

- 全屏 Three.js canvas，桌面为窄侧栏 + 主视口，手机为可折叠底部面板。
- 图层用 checkbox；机位用四段式控制；重置/全景按钮使用本地 Lucide 图标和 tooltip。
- 点选对象只显示名称、尺寸、状态、来源，不显示使用说明性大段文案。
- 使用中性灰、木色、砖红、蓝绿警示的多色体系；无渐变、装饰球或嵌套卡片。
- canvas 尺寸由容器约束，面板不得遮挡视图或溢出屏幕。

- [ ] **Step 4: 复制固定版本浏览器依赖**

构建脚本从独立 node_modules 复制：`three.module.js`、`OrbitControls.js`、`GLTFLoader.js`、Three LICENSE，以及 Lucide 的 `maximize.svg`、`rotate-ccw.svg`、`panel-left.svg`。

- [ ] **Step 5: 构建并运行测试确认 GREEN**

Run: `node scripts/build_rooftop_universal_model_v01.mjs`

Run: `node --test tests/test_rooftop3d_viewer.mjs`

Expected: PASS；查看器不依赖外部 URL。

- [ ] **Step 6: 提交 Task 3**

```powershell
git add -- tests/test_rooftop3d_viewer.mjs src/rooftop3d/viewer scripts/build_rooftop_universal_model_v01.mjs output/空间真值/三维模型/候选_v01_20261010/viewer
git commit -m "feat: add rooftop 3d model viewer"
```

### Task 4: 浏览器视觉核验与交付报告

**Files:**
- Create: `output/空间真值/三维模型/候选_v01_20261010/01_俯视核验.png`
- Create: `output/空间真值/三维模型/候选_v01_20261010/02_轴测核验.png`
- Create: `output/空间真值/三维模型/候选_v01_20261010/03_V01-R1核验.png`
- Create: `output/空间真值/三维模型/候选_v01_20261010/04_V02-R1核验.png`
- Create: `output/空间真值/三维模型/候选_v01_20261010/README_模型单位与使用边界.md`
- Create: `output/空间真值/三维模型/候选_v01_20261010/楼顶通用三维模型_v01_候选核验报告.md`

- [ ] **Step 1: 启动本地静态服务器**

Run: `python -m http.server 49344 --directory output/空间真值/三维模型/候选_v01_20261010`

Expected: `http://localhost:49344/viewer/` 返回200；若端口被占用，选择空闲端口并记录。

- [ ] **Step 2: 用内置浏览器执行桌面/手机检查**

- 桌面：1440×1000；手机：390×844。
- 检查 canvas 像素非空且非单色，模型包围盒完整入镜。
- 切换四个预设机位并分别截图。
- 手机端至少核对一次面板展开、收起、四个机位按钮和对象信息区；截图可保留为临时验收证据，最终包仍交付四张固定机位截图。
- 切换天花层，确认默认关闭、开启后显示2450/2700控制面。
- 点选四柱、茶室背景墙、吧台和设备对象，确认信息面板与 extras 一致。
- 检查按钮、标签和面板无重叠或溢出。

- [ ] **Step 3: 写 README 和核验报告**

README 必须声明 GLB 用米、OBJ用毫米、坐标轴映射、导入设置、候选状态和非施工用途。报告逐项记录 `pass/fail/uncertain/not_visible`，并记录桌面与手机验收视口、canvas像素检查、文件大小、SHA-256和300mm天花冲突。

- [ ] **Step 4: 运行全部自动回归**

```powershell
$env:PYTHONUTF8='1'
python tmp/geometry/test_render_rooftop_whole_floor_truth_model_v03.py
python tmp/geometry/test_render_rooftop_whole_floor_truth_model_v04.py
node --test tests/test_rooftop3d_scene.mjs tests/test_rooftop3d_exports.mjs tests/test_rooftop3d_viewer.mjs
```

Expected: 五个测试入口全部 PASS。

- [ ] **Step 5: 文件级最终核验**

检查 GLB/OBJ/MTL/manifest/README/报告和四张 PNG 均存在、非空且可读取；重新计算 SHA-256；确认历史 v03/v04 文件时间与哈希未被覆盖。

- [ ] **Step 6: 提交 Task 4**

```powershell
git add -- output/空间真值/三维模型/候选_v01_20261010
git commit -m "test: verify rooftop universal 3d model"
```
