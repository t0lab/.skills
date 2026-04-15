---
name: pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) — AND use the generator/evaluator workflow below |
| Measure alignment / spacing | `python scripts/measure.py output.pptx` (see [Alignment Measurement](#alignment-measurement)) |
| Check overlaps + header/footer clearance | `python scripts/invariants.py output.pptx` (pure ruler, no judgments — reviewer applies thresholds) |

---

## Three-agent workflow (REQUIRED when creating a deck)

LLMs are biased-generous about their own work — the same agent cannot reliably plan, build, and judge a deck. Creating a .pptx is split into three roles running in **separate contexts**:

1. **Content creator** — [agents/content-creator.md](agents/content-creator.md). Writes `<deck>.spec.md`: content (exact strings), design direction (palette/fonts/motif), alignment contracts. Produces no code, touches no .pptx.
2. **Code generator** — [agents/code-generator.md](agents/code-generator.md). Reads `spec.md`, writes pptxgenjs code, builds `<deck>.pptx` + `<deck>.js`. Assigns semantic `objectName` to every shape, matching names in the spec.
3. **Slide reviewer** — [agents/slide-reviewer.md](agents/slide-reviewer.md). Runs in a **fresh subagent** (no creation/generation transcript). Receives deck + spec + user intent. Grades against hard thresholds, returns PASS/FAIL with exact fixes.

### Orchestrator loop (what the main skill agent does)

```
user asks for a deck
  └─ Agent(pptx-content-creator): write spec.md
       ↓ returns spec.md path + one-paragraph user intent
  └─ Agent(pptx-code-generator): read spec, write .js + .pptx, self-check
       ↓ returns deck path + js path
  └─ Agent(pptx-slide-reviewer) in FRESH subagent: grade deck against spec
       ↓
       PASS → return deck to user
       FAIL → SendMessage(pptx-code-generator) with punch list, rebuild, re-dispatch reviewer
       ↓
       loop up to 9 review iterations; if still FAIL, surface to user with last report
```

- The orchestrator NEVER passes the creator's or generator's reasoning/transcript to the reviewer — only deck, spec, user intent.
- Neither the creator nor the generator may self-approve.
- "Intentional" in the generator's head means nothing. If the contract is in spec.md, the reviewer grades it. If not, it isn't a contract. Intentional exceptions belong in the spec's "Intentional exceptions" section — not in the generator's justification.
- If the generator believes the spec is impossible or contradictory, it surfaces that to the orchestrator; only the content creator may edit the spec.

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

**Always go through the generator/evaluator loop above — do not build a deck yourself in the main context, and do not skip the reviewer even for "quick" decks.** Every shape must have a semantic `objectName` (see pptxgenjs.md's Shape Naming section).

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Alignment Measurement

`scripts/measure.py` is the agent's **"eyes"** — a static geometry ruler that replaces the drag-time Smart Guides a human gets in Canva/Figma. Because the agent has no UI feedback loop, alignment errors (centering a text box inside a shape, matching a border's corner radius to its inner shape, equal-spacing a row of cards) are almost always rounding/arithmetic mistakes that visual QA cannot catch at 2–3 pixel precision.

The script is a **ruler, not a judge** — it emits raw measurements and lets the agent decide what is a mistake vs. intentional. No severity levels, no auto-fix, no "expected values". Just numbers.

### Usage

```bash
python scripts/measure.py output.pptx                  # text report, all slides
python scripts/measure.py output.pptx --json           # JSON for parsing
python scripts/measure.py output.pptx --slide 3        # single slide
python scripts/measure.py output.pptx --shape Card1    # single shape + relations
python scripts/measure.py unpacked/                    # also accepts an unpacked directory
```

### What the report contains per shape

- **Bbox + geometry**: `x, y, cx, cy`, center, `prstGeom`, `roundrect_adj`, computed corner radius in EMU
- **Text body**: `anchor`, `anchorCtr`, inset (L/T/R/B), whether it contains real text
- **Slide-level distances**: gap to each slide edge, delta to slide center
- **Parent-child** (inferred from `<p:grpSp>` if present, else bbox containment + z-order):
  - `gap_to_parent_edges` (L/R/T/B)
  - `center_delta_from_parent_center` (raw and padding-aware)
  - `parent_roundrect_corners`: for each of the 4 rounded corners, how much the child bbox intrudes into the corner square — detects accent bars / side borders overflowing a rounded parent
- **Concentric outer**: if a larger shape shares the child's center with lower z-order (border/outer pattern), reports its corner radius and the *ideal* outer radius to properly enclose the inner roundness
- **Siblings** (up to 10 nearest, non-overlapping peers under the same parent):
  - `gap_emu` (horizontal/vertical)
  - `edge_alignments_emu` (10 relations: L-L, R-R, T-T, B-B, center X/Y, and opposite-edge pairs)
  - `size_delta_emu`

### When to run

Run `measure.py` as part of the build/test loop, BEFORE visual QA:

```
edit → measure.py → fix numeric issues → pack → render JPG → subagent visual QA
```

`measure.py` catches numeric alignment errors (rounding, off-by-few-EMU, corner-radius mismatch, padding-unaware centering). Visual QA catches design-level issues (contrast, overflow text, boring layouts). Use both.

Agents should read the relevant numbers and decide themselves — a `center_delta` of a few hundred EMU is almost certainly a rounding bug to fix; a delta of tens of thousands of EMU may be an intentional layout choice.

### Running is not reading

Invoking `measure.py` and then moving on without inspecting the output is not verification — it is a ritual. If you pipe the report to `head -60`, skim structure, and declare the file built, you have done nothing.

### Required: slide-by-slide, shape-by-shape review

Run per-slide and read each slide's output in full:

```bash
python3 scripts/measure.py output.pptx --slide 1 > /tmp/s1.txt
python3 scripts/measure.py output.pptx --slide 2 > /tmp/s2.txt
# etc.
```

For **every slide**, go through each shape and check:

1. **Shapes with `children_alignment`** — for each child, read `padding_aware_center_delta_emu`. Ask: "should this child be centered in the parent?" If yes and `dx` or `dy` ≠ 0, that is a bug unless you can name the reason it is intentional.

2. **`candidate_row_pairs`** — for each pair, ask: "did I intend these two to share the same horizontal center line?" If yes and `cY_delta` ≠ 0, fix it. Ignore pairs that involve a full-height decorative bar (accent bar, divider) — its center is mid-container by design, not a row position.

3. **`candidate_column_pairs`** — same, for vertical alignment. "Did I intend these to share the same vertical center line?" If yes and `cX_delta` ≠ 0, fix it.

4. **`any_corner_overlap: True`** — accent bar or border is poking into a rounded parent corner. Fix or swap parent to `RECTANGLE`.

5. **Key sibling pairs** — for every pair of elements you *designed* to be on the same row or column (icon + label, header title + page number, stat number + caption), look up their `cX` / `cY` in the siblings block and confirm it is 0 (or a deliberate offset you can justify).

Do not skim. Do not stop at the first clean slide. Go through all slides.

**When you find a number, write a verdict in your reply.** Example:
```
Slide 2, card [4] child 'GitHub Copilot' padding_aware dy=-173736 → title is 0.19" above card center, subtitle dy=146304 → 0.16" below. Asymmetric: fix by equalizing y positions of title/subtitle around card midpoint.
Slide 2, card [4] child 'Shape 3' (accent bar) padding_aware dx=-1293876 → intentional, bar sits flush left inside card.
```

No verdict = no verification. "All intentional" with no explanation per shape is not accepted.

### Interpreting sibling `cX` / `cY` deltas

The most frequent failure mode is elements that *look* like they should share a center line but don't — an icon next to a title, a slide-number label next to the slide heading, a badge next to a stat value. `measure.py` surfaces this as a small non-zero `cX` or `cY` in the sibling block.

Rule of thumb when scanning sibling output:

- **Two siblings that visually belong in one row/column** (icon + label, title + pill, header + page-number) — if their `cY` (row) or `cX` (column) differs by anything non-zero, treat it as a bug unless you deliberately offset them. 10000–50000 EMU (~0.01–0.05") is the danger zone: small enough to miss by eye on the coordinate math, large enough to look wrong on the rendered slide.
- **Two siblings that are not meant to align** (e.g. a footer bar and a corner ornament) — ignore their `cX`/`cY` delta; it's meaningless.
- The tool cannot know your intent. You have to ask "did I *want* these two to line up?" for each sibling pair the report surfaces.

Common patterns that produce small cY mismatches in generated slides:
- One element has `valign: "middle"` and the other doesn't — the first centers text in its box, the second top-anchors. If their boxes don't share `y` and `h`, centers diverge.
- Two elements with the same `y` but different `h` — centers differ by `(h_a - h_b) / 2`.
- Icon placed at `card.y + pad` with `h = H_icon` next to text placed at `card.y + pad'` with `h = H_text`. Unless `pad + H_icon/2 == pad' + H_text/2`, the centers miss.

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `pip install Pillow` - thumbnail grids
- `npm install -g pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images
