---
name: pptx-dbx
description: "Use this skill any time a .pptx file is involved while the agent is running inside a Databricks notebook (Genie Code, Databricks Assistant in Agent mode, or any notebook-driven pipeline). This includes: creating slide decks / pitch decks / presentations from a notebook; reading/parsing/extracting text from a .pptx stored on a Unity Catalog Volume, Workspace file, or DBFS; editing existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, comments; producing .pptx and .pdf deliverables and putting them on a Volume so the user can download them via Catalog Explorer. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" \"pptx,\" \"powerpoint,\" or names a .pptx file in a Databricks notebook context. The toolchain is python-pptx + %pip + dbutils + Volumes — do not try to use Node.js, npm, or local-filesystem assumptions."
license: Proprietary
---

# PPTX on Databricks

A skill for creating, editing, and inspecting PowerPoint files from inside a Databricks notebook. The agent doing the work is typically Genie Code in Agent mode — it writes Python cells, runs them, reads outputs, and hands the final file to the user via a Unity Catalog Volume.

The skill is built around three ideas:

1. **Specs are the contract.** Every deck starts with `<deck>.spec.md` — exact strings, palette, fonts, alignment contracts. The deck is graded against the spec, not against vibes.
2. **Geometry is measurable.** A pure-Python ruler (`scripts/measure.py`) and an invariants checker (`scripts/invariants.py`) tell you whether shapes line up. They are the agent's "eyes" — Databricks notebooks often have no way to render slides to images, so structural QA is the only QA you are guaranteed to have.
3. **Three roles, fresh contexts.** A single LLM cannot reliably plan, build, and judge its own deck. The skill splits the work into a content creator, a code generator, and a reviewer — each running with a clean context window.

## Read this before anything else

**[references/databricks.md](references/databricks.md)** — environment guide. Covers compute types, install/restart sequence, where to write files so the user can download them, how visual QA degrades on serverless, and Genie-Code-specific quirks. Read this first on any new task; it determines what is and isn't possible in your notebook.

## Quick reference

| Task | Where to look |
|------|---------------|
| Set up packages in a notebook cell | [references/databricks.md](references/databricks.md) §2 — and the [assets/notebook_template.ipynb](assets/notebook_template.ipynb) starter |
| Create a deck from scratch | [references/python-pptx.md](references/python-pptx.md) — AND the three-agent loop below |
| Edit / templatize an existing deck | [references/editing.md](references/editing.md) |
| Pick palette, fonts, motif, spacing | [references/style.md](references/style.md) |
| Read text out of a .pptx | `python -m markitdown /Volumes/.../deck.pptx` (after `%pip install "markitdown[pptx]"`) |
| Measure alignment | `python scripts/measure.py /Volumes/.../deck.pptx` (see [Alignment measurement](#alignment-measurement)) |
| Find overlaps + header/footer collisions | `python scripts/invariants.py /Volumes/.../deck.pptx` |
| Render to images for visual QA | [references/databricks.md](references/databricks.md) §5 (LibreOffice / Aspose / skip) |
| Hand the deck to the user | [references/databricks.md](references/databricks.md) §6 |

All scripts in `scripts/` are pure Python — they run unmodified in any Databricks compute that can run Python (classic, serverless, jobs). The only external binaries are `soffice` (LibreOffice) and `pdftoppm` (poppler), and both are optional.

---

## Three-role workflow (REQUIRED when creating a deck)

LLMs are biased-generous about their own work. The model that wrote the spec sees its own rationale; the model that wrote the code remembers what it intended; neither can grade the result honestly. The skill enforces three roles in three separate contexts:

1. **Content creator** — [agents/content-creator.md](agents/content-creator.md). Writes `<deck>.spec.md`: every string the deck must contain, the palette/fonts/motif (chosen from [references/style.md](references/style.md)), and the alignment contracts the reviewer will grade against. Writes no code, touches no .pptx.

2. **Code generator** — [agents/code-generator.md](agents/code-generator.md). Reads `spec.md`, writes `<deck>.py`, builds `<deck>.pptx` at the Volume path the spec names. Every shape gets a semantic `name` matching the names in the spec — without this, the reviewer cannot map measurements back to design intent and auto-FAILs the deck.

3. **Slide reviewer** — [agents/slide-reviewer.md](agents/slide-reviewer.md). Runs in a **fresh subagent** with no creator/generator transcript. Receives only deck path, spec path, and the user's one-paragraph intent. Grades against hard thresholds. Returns PASS or FAIL with exact fixes — no soft passes.

### Orchestrator loop

```
user asks for a deck in a Databricks notebook
  └─ (read references/databricks.md — install packages, decide output Volume path)
  └─ Agent(pptx-dbx-content-creator): write spec.md
       ↓ returns spec.md path + one-paragraph user intent
  └─ Agent(pptx-dbx-code-generator): read spec, write .py + .pptx, self-check
       ↓ returns deck path + py path
  └─ Agent(pptx-dbx-slide-reviewer) in FRESH subagent: grade deck against spec
       ↓
       PASS → deliver deck to user (print Volume path + Catalog Explorer hint)
       FAIL → SendMessage(pptx-dbx-code-generator) with punch list, rebuild, re-dispatch reviewer
       ↓
       loop up to 9 review iterations; if still FAIL, surface to user with last report
```

Discipline:
- The orchestrator NEVER passes the creator's or generator's reasoning to the reviewer — only deck, spec, user intent.
- Neither the creator nor the generator may self-approve.
- "Intentional" in the generator's head means nothing. If a contract is in spec.md, the reviewer grades it. If not, it isn't a contract. Intentional exceptions belong in the spec's "Intentional exceptions" section — not in the generator's justification.
- If the generator believes the spec is impossible or contradictory, it surfaces that to the orchestrator; only the content creator may edit the spec.

### How to dispatch each role: one role = one LLM call

**There is no public API to spawn another Genie Code session from a notebook.** Genie Code is a UI assistant (chat panel + `Cmd+I` in cells) — Databricks does not expose a "start another Genie Code" SDK call. (Note: **AI/BI Genie** is a different product for SQL/table Q&A and does have `WorkspaceClient().genie.start_conversation_and_wait(...)`, but it cannot run python-pptx and is not what we need here.)

To get a programmatically-isolated subagent, call the same Claude model that powers Genie Code via **Databricks Model Serving** (or the Anthropic API directly). Each call:

1. Loads `agents/<role>.md` as the **system prompt** — this is the role brief.
2. Sends ONLY the role's allowed inputs as the **user message** — no prior-cell context.
3. Returns the model's output, which is the subagent's work product.

Because each call is stateless, the role is isolated by construction — no memory of any prior cell or role.

#### Fallback: single-agent mode (when `DBX_ENDPOINT` is not set)

If no Model Serving endpoint is configured, the notebook prints `MULTI-AGENT DISABLED` and falls back to **single-agent mode**: the Genie Code session driving the notebook plays all three roles itself, serially, in the same cells. The `dispatch_subagent` helper still runs — but instead of calling a model, it prints the role brief + the inputs the role is allowed to see and returns `None`. The role cell then expects the artifact (spec.md, .pptx, review.md) to be produced inline by Genie Code (or a human) before re-running the gating assertion.

Discipline rules in single-agent mode:

1. **Do not skip the role separation.** Even though the same brain plays every role, treat each role cell as a fresh start. Re-read the role brief and the inputs printed by `dispatch_subagent` — do not rely on memory of what you decided in the previous cell.
2. **Spec on disk is still the contract.** The reviewer role re-reads `spec.md` and the deck — it does NOT consult its own memory of "what I meant to build."
3. **Re-review = re-run the cell.** Each re-run is a new reviewer pass; do not paste the prior review into your reasoning, even though it's still in `REVIEW_PATH`. Re-grade independently.
4. **Acknowledge the weakness in the final handoff.** Single-agent mode is structurally weaker than true multi-agent. State in the deliverable: "Built in single-agent mode — same model played creator/generator/reviewer roles." This signals to the user that visual/judgment QA is less independent than a multi-agent build.

Switch to multi-agent (set `DBX_ENDPOINT`) whenever the deck is high-stakes or you want a genuinely independent review.

The pattern for every role cell:

```python
# === Role: <pptx-dbx-content-creator | code-generator | slide-reviewer> ===
# Read the role brief from disk (do NOT carry prior reasoning into this cell).
ROLE_BRIEF = open(f"{SKILL_DIR}/agents/<role>.md").read()
# Inputs the role is allowed to see:
SPEC_PATH = "/tmp/<deck>.spec.md"   # always
DECK_PATH = "/Volumes/.../<deck>.pptx"  # generator + reviewer only
USER_INTENT = "<one paragraph, same wording every cell>"
# Then: act as that role, using ONLY the role brief + the inputs above.
```

What each cell receives, and what it must NOT receive:

| Role cell | Receives | Must NOT receive |
|---|---|---|
| `content-creator` | user intent, `references/style.md` | nothing else |
| `code-generator` | `spec.md`, `references/python-pptx.md` | the creator's reasoning, the spec's draft history |
| `slide-reviewer` | `deck.pptx`, `spec.md`, user intent (one paragraph) | the creator's transcript, the generator's transcript, "the generator says X is intentional", any prior reviewer report |

The reviewer cell is the strictest: it must form an independent judgment. If a build fails review, the **fix-and-rebuild** loop is two more cells:

```text
Cell K   : code-generator cell, given spec.md + the reviewer's punch list → writes a new .pptx
Cell K+1 : a FRESH slide-reviewer cell, given only deck + spec + user intent (NOT the punch list, NOT the prior reviewer report) → grades again
```

Each re-review is a brand-new reviewer cell. Carrying the previous review forward biases the new one toward confirming the fixes were applied, instead of independently checking the deck.

#### Why "cell = subagent" works on Databricks

Genie Code's per-cell execution naturally creates the context boundary that subagents create elsewhere. As long as the cell starts by re-reading the role brief and the inputs from disk — and you do NOT paste prior reasoning into the cell prompt — the role is effectively isolated. The discipline is in what you put **into** the cell, not the mechanism itself.

The notebook template ([assets/notebook_template.ipynb](assets/notebook_template.ipynb)) implements this: §2b defines `dispatch_subagent(role, user_message)` (Databricks Model Serving by default, Anthropic API as fallback). §3, §4, §7 each call it once with the role-appropriate inputs. Re-running §7 spawns a brand-new reviewer subagent — that's the fix-and-rebuild loop.

---

## Notebook starter

[assets/notebook_template.ipynb](assets/notebook_template.ipynb) is a ready-to-import Jupyter notebook (Databricks: Workspace → Import → File). Cells, in order:

1. Install Python packages (`%pip install`).
2. `dbutils.library.restartPython()`.
3. Imports + path constants.
4. Run the content-creator (write `spec.md`).
5. Run the code generator (write `.py` + `.pptx`).
6. Run structural QA (`measure.py`, `invariants.py`).
7. Optionally render to images (LibreOffice / Aspose).
8. Run the reviewer.
9. Deliver — print the Volume path; show the Catalog Explorer download hint.

Genie Code can read this template, adapt the placeholders, and run it. Even if you skip the template, the cell ordering it captures is the right ordering to follow manually.

---

## Reading content from an existing deck

```python
%pip install "markitdown[pptx]"
```
```python
dbutils.library.restartPython()
```
```python
import subprocess
out = subprocess.run(
    ["python", "-m", "markitdown", "/Volumes/main/default/decks/input.pptx"],
    capture_output=True, text=True,
)
print(out.stdout)
```

For raw XML inspection (when you need to see formatting, masters, notes):

```python
!python /Workspace/Repos/<user>/pptx-dbx/scripts/office/unpack.py /Volumes/.../input.pptx /tmp/unpacked/
```

---

## Editing an existing deck

**Read [references/editing.md](references/editing.md).** Two modes:

- **python-pptx edit-in-place** — open, walk shapes, replace text, save. Best for content updates where the template's structure is correct.
- **XML unpack/edit/pack** — when the change is structural (delete a slide, reorder, deep formatting) or python-pptx doesn't expose the attribute.

Path discipline: input from a Volume, scratch in `/tmp/unpacked/`, output back to a Volume. Never deliver from `/tmp/` — it vanishes when the cluster detaches.

---

## Creating from scratch

**Read [references/python-pptx.md](references/python-pptx.md).** Use when no template or reference deck is available.

Always go through the three-role loop above. Do not build a deck yourself in the main context, do not skip the reviewer even for "quick" decks, and do not save to a non-Volume path even for "test" runs — the user will ask for the file and `/tmp/` will be gone.

Every shape gets a semantic `name`. Without it, `measure.py` reports `Rectangle N` / `TextBox N` instead of `StatCard_MarketSize_Value`, and the reviewer cannot grade against spec.md contracts. See [references/python-pptx.md](references/python-pptx.md) §3 for the naming pattern.

---

## Design direction

**See [references/style.md](references/style.md).** Color palettes (including five Databricks-aware ones — Delta Warehouse, Lakehouse Dawn, Notebook Graphite, Genie Ink, Pipeline Mint), header/body font pairings, sizes table, spacing rules, motif menu, common mistakes.

The content creator picks from style.md (or invents in the same spirit) and records the choice in `spec.md`. The code generator reads the choice from `spec.md` — **not from style.md** — because the spec is the single source of truth.

---

## QA (required)

**Assume there are problems. Your job is to find them.** Your first build is almost never correct. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```python
!python -m markitdown /Volumes/.../deck.pptx
!python -m markitdown /Volumes/.../deck.pptx | grep -iE "xxxx|lorem|ipsum|placeholder|this.*(page|slide).*layout" || echo "no leftover placeholders"
```

If the grep returns hits, fix them before declaring success.

### Structural QA — always available

```python
!python scripts/invariants.py /Volumes/.../deck.pptx > /tmp/inv.txt
!python scripts/measure.py /Volumes/.../deck.pptx --slide 1 > /tmp/s1.txt
# ... per slide
```

These are pure Python. They work on every Databricks compute type. There is no excuse to skip them. The reviewer treats their absence as a build failure.

### Visual QA — best-effort

Visual QA requires rendering slides to images. Databricks notebooks do NOT have LibreOffice preinstalled, and on **serverless compute you cannot install it** (`%sh apt-get` is sandboxed). Strategies, in order of preference:

1. **Classic compute, install once**: `%sh sudo apt-get install -y libreoffice poppler-utils`, then use `scripts/office/soffice.py` + `pdftoppm`.
2. **Aspose.Slides** (Python, works on serverless): `%pip install aspose-slides`. Free tier watermarks slide 1 — fine for QA, do NOT ship the Aspose-rendered PDF.
3. **Skip visual QA**: rely on structural QA + careful content re-read. The reviewer must state explicitly in the final report that visual QA was skipped — a structural PASS does NOT imply a visual PASS.

See [references/databricks.md](references/databricks.md) §5 for exact commands.

### Verification loop

1. Generate slides → structural QA → fix numeric issues → rebuild
2. If rendering is available: render → inspect with a fresh-context subagent → fix → re-render affected slides
3. **List issues found.** If none found, look again more critically.
4. Repeat until a full pass surfaces no new issues.

Do not declare success on the strength of `prs.save()` alone. A clean build with 200 lines of unread `measure.py` output is indistinguishable from a broken build.

---

## Alignment measurement

`scripts/measure.py` is the agent's **eyes** — a static geometry ruler that replaces the drag-time Smart Guides a human gets in PowerPoint or Figma. The agent has no UI feedback loop; alignment errors (centering a label inside a card, matching a border's corner radius to its inner shape, equal-spacing a row of cards) are nearly always rounding/arithmetic mistakes invisible to coarse visual QA.

The script is a **ruler, not a judge**. It emits raw measurements; the reviewer applies thresholds. There are no severity levels, no auto-fix, no "expected values" baked in — just numbers. (This division of labor is deliberate; do not extend `measure.py` to flag issues.)

### Usage

```python
!python scripts/measure.py /Volumes/.../deck.pptx                 # text report, all slides
!python scripts/measure.py /Volumes/.../deck.pptx --json          # JSON
!python scripts/measure.py /Volumes/.../deck.pptx --slide 3       # one slide
!python scripts/measure.py /Volumes/.../deck.pptx --shape Card1   # one shape + relations
!python scripts/measure.py /tmp/unpacked/                         # also accepts an unpacked dir
```

### What the report contains per shape

- **Bbox + geometry**: `x, y, cx, cy`, center, `prstGeom`, `roundrect_adj`, computed corner radius (EMU).
- **Text body**: `anchor`, `anchorCtr`, inset (L/T/R/B), whether it has real text.
- **Slide-level distances**: gap to each slide edge, delta to slide center.
- **Parent-child** (inferred from `<p:grpSp>` if present, else bbox containment + z-order):
  - `gap_to_parent_edges` (L/R/T/B)
  - `center_delta_from_parent_center` (raw and padding-aware)
  - `parent_roundrect_corners`: how much each child corner intrudes into the parent's rounded-corner square — detects accent bars / borders overflowing a rounded parent.
- **Concentric outer**: if a larger shape shares the child's center with lower z-order (border/outer pattern), reports its corner radius and the *ideal* outer radius to properly enclose the inner roundness.
- **Siblings** (up to 10 nearest, non-overlapping peers under the same parent):
  - `gap_emu` (horizontal/vertical)
  - `edge_alignments_emu` (L-L, R-R, T-T, B-B, center X/Y, opposite-edge pairs)
  - `size_delta_emu`

### When to run

```
build → measure.py → fix numeric issues → invariants.py → fix overlaps → (render if possible) → reviewer
```

### Running is not reading

Invoking `measure.py` and moving on is not verification — it is a ritual. If you pipe to `head -60`, skim, and declare the file built, you have done nothing.

**Required: slide-by-slide, shape-by-shape review.**

```python
!python scripts/measure.py /Volumes/.../deck.pptx --slide 1 > /tmp/s1.txt
!python scripts/measure.py /Volumes/.../deck.pptx --slide 2 > /tmp/s2.txt
# etc.
```

For every slide, for every shape, check:

1. **`children_alignment` → `padding_aware dx/dy`** — for each child, ask: "should this be centered in the parent?" If yes and `dx` or `dy` ≠ 0, that is a bug unless you can name a reason it is intentional.
2. **`candidate_row_pairs` → `cY_delta`** — "did I intend these to share a horizontal centerline?" Ignore full-height decorative bars. For all content pairs: 0 = correct, non-zero = fix.
3. **`candidate_column_pairs` → `cX_delta`** — same for vertical centerlines.
4. **`any_corner_overlap: True`** — accent bar or border is poking into a rounded parent corner. Fix or swap parent to `RECTANGLE`.
5. **Key sibling pairs you designed** (icon + label, header title + page number, stat number + caption) — look up `cX` / `cY` in the siblings block and confirm 0 (or a deliberate offset you can justify).

**Write a verdict per shape, per slide, in your reply.** "All intentional" with no per-shape explanation is not accepted. No verdict = no verification. "measure.py ran with no errors" is also not verification — the tool almost never errors.

### Interpreting sibling deltas

The most frequent failure mode is elements that *look* like they share a center line but don't — icon next to a title, slide-number next to heading, badge next to a stat. `measure.py` surfaces this as a small non-zero `cX` / `cY` in the sibling block.

- **Two siblings that visually belong in one row/column** (icon + label, title + pill, header + page-number) — if `cY` or `cX` ≠ 0, treat as a bug unless you deliberately offset them. **10000–50000 EMU (≈0.01–0.05") is the danger zone**: small enough to miss in your coordinate math, large enough to look wrong on the rendered slide.
- **Two siblings not meant to align** (footer bar + corner ornament) — ignore.
- The tool cannot know your intent. You have to ask "did I *want* these two to line up?" for each pair.

Common patterns that produce small `cY` mismatches:
- One element has `vertical_anchor = MIDDLE` and the other doesn't — text in the first centers, text in the second top-anchors.
- Two elements with the same `y` but different `h` — centers differ by `(h_a - h_b) / 2`.
- Icon at `card.y + pad_a` with `h = H_icon` next to text at `card.y + pad_b` with `h = H_text`. Unless `pad_a + H_icon/2 == pad_b + H_text/2`, the centers miss.

---

## Delivering the file to the user

Final outputs MUST live on a Unity Catalog Volume (or Workspace file as fallback). `/tmp/` is scratch only.

```python
out = "/Volumes/main/default/decks/quarterly_review.pptx"
print(f"Deck ready: {out}")
print("Download from Catalog Explorer → main → default → decks → right-click → Download")
```

Genie Code surfaces the printed cell output to the user. The user downloads via Catalog Explorer (UI: select file, click Download). There is no public REST URL for a Volume file; do NOT generate fake `/files/...` links for Volume paths — those only work for Workspace files.

If the user asked for PDF, render via LibreOffice (not Aspose, whose free tier watermarks) and place alongside the .pptx on the same Volume.

See [references/databricks.md](references/databricks.md) §6 for the full delivery patterns including Workspace-file fallbacks.

---

## Dependencies

Notebook cell, run once per session:

```python
%pip install python-pptx "markitdown[pptx]" Pillow defusedxml
# optional, for visual QA on serverless:
%pip install aspose-slides
```
```python
dbutils.library.restartPython()
```

Optional system packages (classic compute only, via `%sh`):

```
sudo apt-get install -y libreoffice poppler-utils
```

The full environment matrix is in [references/databricks.md](references/databricks.md) §1.
