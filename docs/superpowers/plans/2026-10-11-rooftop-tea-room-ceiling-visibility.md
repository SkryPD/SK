# Rooftop Tea-room Ceiling Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository's user-supplied `AGENTS.md` forbids subagents, so execution must remain inline in the current thread.

**Goal:** Generate two versioned grey-model images that make the owner-confirmed tea-room ceiling at `Z=2450mm` visibly unambiguous without changing v05 geometry.

**Architecture:** A focused Python renderer imports the existing v05 truth-model module and derives every wall, window and ceiling coordinate from `scene_spec()`. It emits an opaque capped axonometric view and a translucent cutaway view, then writes a compact evidence report. A separate test verifies provenance, dimensions, image decodability and non-destructive output.

**Tech Stack:** Python 3, Pillow, existing v05 truth-scene module

---

### Task 1: Lock the display contract with a failing test

**Files:**
- Create: `tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py`
- Test: `tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py`

- [x] **Step 1: Write the failing test**

```python
module = load_module()
source = module.load_source_scene()
assert source["version"] == "rooftop-whole-floor-truth-model-v05"
assert module.ceiling_contract(source) == {
    "bounds_mm": [34240, 6160, 37440, 10260],
    "ceiling_z_mm": 2450,
    "window_z_range_mm": [350, 2450],
    "head_wall_z_range_mm": [2450, 3020],
}
module.render_all()
assert module.OPAQUE_OUT.exists()
assert module.CUTAWAY_OUT.exists()
```

- [x] **Step 2: Run the test to verify it fails**

Run: `python tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py`

Expected: failure because `render_rooftop_ceiling_visibility_v01.py` does not exist.

### Task 2: Implement the two view-only renders

**Files:**
- Create: `tmp/geometry/render_rooftop_ceiling_visibility_v01.py`
- Read: `tmp/geometry/render_rooftop_whole_floor_truth_model_v05.py`

- [x] **Step 1: Import, do not duplicate, v05 truth geometry**

```python
def load_source_scene() -> dict:
    source = load_v05_module().scene_spec()
    if source["version"] != "rooftop-whole-floor-truth-model-v05":
        raise ValueError("Ceiling visibility renderer requires v05 truth geometry")
    return source
```

- [x] **Step 2: Derive and validate the ceiling contract**

```python
def ceiling_contract(scene: dict) -> dict:
    objects = {item["id"]: item for item in scene["objects"]}
    ceiling = objects["ceiling_level_1_tea_room"]
    window = objects["tea_room_only_window"]
    head = objects["tea_window_head_wall"]
    return {
        "bounds_mm": ceiling["bounds_mm"],
        "ceiling_z_mm": ceiling["height_mm"],
        "window_z_range_mm": [window["z_mm"], window["head_height_mm"]],
        "head_wall_z_range_mm": [head["z_mm"], head["z_max_mm"]],
    }
```

- [x] **Step 3: Render A and B**

Use one local isometric projector for both images. Draw the verified tea-room walls from source objects, then draw the full ceiling polygon opaque for A and alpha-composited with a cutaway corner for B. Add direct labels for `2450mm`, `570mm`, and `3020mm`.

- [x] **Step 4: Write the candidate report**

Record source version, output names, hashes and a hard-constraint matrix. State that the images are display-only and not construction documentation.

### Task 3: Verify outputs and visual legibility

**Files:**
- Test: `tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py`
- Create: `output/空间真值/整层灰模/封顶可视化_候选_v01_20261011/01_茶室完整封顶轴测灰模_v01.png`
- Create: `output/空间真值/整层灰模/封顶可视化_候选_v01_20261011/02_茶室封顶半透明剖切灰模_v01.png`
- Create: `output/空间真值/整层灰模/封顶可视化_候选_v01_20261011/茶室封顶可视化_v01_候选核验报告.md`

- [x] **Step 1: Run the focused test**

Run: `python tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py`

Expected: `PASS`.

- [x] **Step 2: Re-run source regression tests**

Run: `python tmp/geometry/test_render_rooftop_whole_floor_truth_model_v05.py`

Expected: `PASS`.

- [x] **Step 3: Inspect both actual PNG files**

Confirm the ceiling plane is nonblank and visually obvious in A, while B visibly retains the window/head-wall/ceiling relationship. Any obscured hard constraint must be recorded as `not_visible`, not passed by inference.

- [x] **Step 4: Check tracked changes and commit only task files**

```powershell
git diff --check
git status --short
git add docs/superpowers/specs/2026-10-11-rooftop-tea-room-ceiling-visibility-design.md `
  docs/superpowers/plans/2026-10-11-rooftop-tea-room-ceiling-visibility.md `
  tmp/geometry/render_rooftop_ceiling_visibility_v01.py `
  tmp/geometry/test_render_rooftop_ceiling_visibility_v01.py `
  output/空间真值/整层灰模/封顶可视化_候选_v01_20261011
git commit -m "feat: add visible rooftop tea-room ceiling views"
```
