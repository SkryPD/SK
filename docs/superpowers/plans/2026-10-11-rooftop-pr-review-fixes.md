# Rooftop PR Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the PR #1 review blockers without changing the approved rooftop geometry or construction dimensions.

**Architecture:** Preserve the v05 truth-scene JSON as the authoritative design input, propagate measurement uncertainty through model descriptors, GLB extras, manifests, and the offline viewer, and rebuild all versioned packages from the same source. Keep Python verification runnable without pytest by adding a standard-library test runner for the tracked function-style geometry tests.

**Tech Stack:** Node.js test runner, Three.js exporters, browser JavaScript, Python `unittest`, Pillow, NumPy, python-docx, PowerShell/Git.

---

### Task 1: Preserve Tea-Window Plan-Offset Uncertainty

**Files:**
- Modify: `tests/test_rooftop3d_scene.mjs`
- Modify: `tests/test_rooftop3d_exports.mjs`
- Modify: `tests/test_rooftop3d_viewer.mjs`
- Modify: `tmp/geometry/test_render_rooftop_whole_floor_truth_model_v05.py`
- Modify: `tmp/geometry/render_rooftop_whole_floor_truth_model_v05.py`
- Modify: `src/rooftop3d/exporters.mjs`
- Modify: `src/rooftop3d/viewer/app.js`

- [x] **Step 1: Write failing assertions**

Assert that `tea_window_sill_wall`, `tea_window_head_wall`, and `tea_room_only_window` all expose `plan_offset_status: "requires_site_measurement"`; assert that the manifest preserves this field and that the viewer renders a dedicated `平面定位` detail row.

- [x] **Step 2: Verify RED**

Run:

```powershell
node --test tests/test_rooftop3d_scene.mjs tests/test_rooftop3d_exports.mjs tests/test_rooftop3d_viewer.mjs
& $env:CODEX_PYTHON tmp/geometry/test_render_rooftop_whole_floor_truth_model_v05.py
```

Expected: failures for the two dependent wall objects, manifest metadata, and viewer detail row.

- [x] **Step 3: Implement the minimum propagation**

Add `plan_offset_status` to the two dependent v05 wall objects, flatten descriptor metadata into each manifest object entry, and render the following viewer detail:

```javascript
if (data.plan_offset_status) {
  addDetailRow(
    list,
    "平面定位",
    STATUS_LABELS[data.plan_offset_status] || data.plan_offset_status,
    data.plan_offset_status,
  );
}
```

- [x] **Step 4: Verify GREEN**

Rerun the two commands from Step 2 and require zero failures.

### Task 2: Remove Runtime Workstation Paths

**Files:**
- Create: `tests/test_rooftop_portability.py`
- Modify: `tmp/geometry/render_rooftop_whole_floor_truth_model_v05.py`
- Modify: `tmp/geometry/test_render_rooftop_whole_floor_truth_model_v05.py`
- Modify: `src/rooftop3d/exporters.mjs`

- [x] **Step 1: Write portability tests**

Assert that the v05 renderer/test derive the repository root from `__file__`, and that a generated manifest uses a forward-slash repository-relative source path beginning with `output/` and contains no drive-qualified path.

- [x] **Step 2: Verify RED**

Run:

```powershell
& $env:CODEX_PYTHON -m unittest tests.test_rooftop_portability -v
node --test tests/test_rooftop3d_exports.mjs
```

Expected: current hard-coded Python roots and absolute manifest source path fail.

- [x] **Step 3: Implement portable paths**

Use `Path(__file__).resolve().parents[2]` in the two tracked Python files. In `exporters.mjs`, use `relative(ROOT, sourcePath)` and normalize path separators to `/` before writing the manifest.

- [x] **Step 4: Verify GREEN**

Rerun Step 2 and require zero failures.

### Task 3: Preserve Lucide License Text

**Files:**
- Modify: `tests/test_rooftop3d_viewer.mjs`
- Modify: `scripts/build_rooftop_universal_model_v01.mjs`
- Modify: `scripts/build_rooftop_universal_model_v02.mjs`

- [x] **Step 1: Write failing package assertions**

Require `viewer/vendor/LUCIDE-LICENSE.txt` in both v01 and v02 package tests and assert that it contains `ISC License` and the Lucide copyright notice.

- [x] **Step 2: Verify RED**

Run `node --test tests/test_rooftop3d_viewer.mjs` and require failure for the missing license.

- [x] **Step 3: Copy the upstream license**

Define `LUCIDE_PACKAGE_DIR`, derive `icons` from it, and copy `lucide-static/LICENSE` to `viewer/vendor/LUCIDE-LICENSE.txt` in both builders.

- [x] **Step 4: Verify GREEN**

Rerun the viewer test and require zero failures.

### Task 4: Provide One Complete Python Test Entry Point

**Files:**
- Create: `requirements.txt`
- Create: `scripts/python_test_runner.py`
- Create: `tests/test_python_test_runner.py`
- Create: `.github/workflows/verify.yml`

- [x] **Step 1: Write failing discovery tests**

Require the runner to discover every zero-argument `test_*` function in the two tracked `tmp/geometry/test_*.py` files, and require `requirements.txt` to declare `numpy`, `Pillow`, and `python-docx`.

- [x] **Step 2: Verify RED**

Run `python -m unittest tests.test_python_test_runner -v` and require failure because the runner and dependency file do not yet exist.

- [x] **Step 3: Implement the runner**

Use `unittest.defaultTestLoader.discover("tests")` for class-based tests, import each tracked function-style geometry test module with `importlib`, wrap each zero-argument `test_*` function in `unittest.FunctionTestCase`, and run the combined suite with `verbosity=2`.

Add a GitHub Actions workflow that installs the pinned Python requirements and the locked Node dependencies, then runs the same Python, Node, syntax, compile, and whitespace checks used locally.

Pin the verified environment versions:

```text
numpy==2.3.5
Pillow==12.3.0
python-docx==1.2.0
```

- [x] **Step 4: Verify GREEN**

Run:

```powershell
& $env:CODEX_PYTHON scripts/python_test_runner.py
```

Expected: all class-based and function-style Python tests execute with zero failures.

### Task 5: Rebuild Packages and Clear Repository Checks

**Files:**
- Regenerate: `output/空间真值/整层灰模/候选_v05_20261011/*`
- Regenerate: `output/空间真值/三维模型/候选_v01_20261010/*`
- Regenerate: `output/空间真值/三维模型/候选_v02_20261011/*`
- Regenerate: `output/空间真值/三维模型/候选_v03_20261011/*`
- Modify: affected package reports and README hashes
- Normalize: the three files reported by `git diff --check`

- [x] **Step 1: Regenerate authoritative artifacts**

Run the v05 renderer, then the v01, v02, and v03 package builders. Preserve the four manually authored v03 report/screenshot files.

- [x] **Step 2: Refresh documented hashes**

Recalculate source, GLB, OBJ, MTL, manifest, report, and screenshot hashes referenced by the tracked reports. Keep the explicit rule that v03 geometry equals v02 geometry.

- [x] **Step 3: Normalize whitespace**

Remove the two Markdown EOF blank lines and regenerate/normalize the archived v01 `three.core.js` so `git diff --check origin/main...HEAD` returns no findings.

- [x] **Step 4: Run the complete verification gate**

Run:

```powershell
& $env:CODEX_PYTHON scripts/python_test_runner.py
node --test (Get-ChildItem tests -Filter '*.mjs' | Select-Object -ExpandProperty FullName)
node --check <each src/scripts/tests JS or MJS file>
& $env:CODEX_PYTHON -m compileall -q scripts tests tmp/geometry
git diff --check origin/main...HEAD
git grep -n -I -E '(sk-[A-Za-z0-9_-]{20,}|api[_-]?key[[:space:]]*[:=])'
```

Also rebuild v03 into a fresh temporary directory, compare all generated core files by SHA-256 against the archived package, and verify the GLB/OBJ/MTL files against their manifest entries.

- [x] **Step 5: Commit and push without merging**

Stage only files belonging to this plan, commit with `fix: harden rooftop truth model package`, push `codex/spa-c-3d`, and recheck PR #1 state. Do not merge.
