# Creating Decks with python-pptx

This file documents the subset of `python-pptx` the code generator should use, the shape-naming convention the reviewer depends on, and the pitfalls that bite most often when translating a spec into code.

---

## 1. Setup

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
```

Create a blank 16:9 deck:

```python
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

Use a blank layout (no default placeholders — you are doing everything manually so the spec controls geometry precisely):

```python
blank = prs.slide_layouts[6]  # "Blank" in the default template
slide = prs.slides.add_slide(blank)
```

---

## 2. Units

python-pptx uses **EMU** (English Metric Units) internally. `914400 EMU = 1 inch`. Helpers:

- `Inches(1.5)` → 1371600 EMU
- `Pt(18)` → 228600 EMU
- `Emu(50000)` → 50000 EMU

Always use `Inches` / `Pt` when writing the generator — the code reads more clearly, and `measure.py` outputs EMU so you can cross-check.

---

## 3. Shape naming (REQUIRED)

Every shape you add MUST get a semantic name that matches what `spec.md` refers to. `python-pptx` assigns names like `"Rectangle 3"` by default — these are useless to the reviewer.

```python
shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(1), Inches(3), Inches(2))
shp.name = "StatCard_MarketSize_Container"  # REQUIRED
```

For text boxes:

```python
tb = slide.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(2.6), Inches(0.5))
tb.name = "StatCard_MarketSize_Value"
```

For pictures:

```python
pic = slide.shapes.add_picture("/Volumes/.../logo.png", Inches(0.5), Inches(0.5), width=Inches(1.5))
pic.name = "Header_Logo"
```

**Pattern**: `<Section>_<Purpose>_<Role>`

- **Section**: `Header`, `Footer`, `StatCard`, `ComponentCard`, `Timeline`, `ComparisonTable`, `TitleBlock`, `SideBar`, `Legend`
- **Purpose**: the specific instance — `LLMCore`, `MarketSize`, `Row3`, `Risk1`, or a 1-based index for generic instances (`Card1`, `Card2`)
- **Role**: what the shape IS — `Container`, `Title`, `Value`, `Label`, `Badge`, `AccentBar`, `Icon`, `Description`, `Separator`, `Background`

Use underscores (not hyphens) so names are valid XML identifiers and easy to grep. Match the spec's spelling exactly — the reviewer does a text match.

If you miss this on any shape, `measure.py` will print `Shape N` / `TextBox N` and the reviewer will FAIL the whole deck.

---

## 4. The primitives you actually need

### 4a. Rectangle / rounded rectangle

```python
from pptx.enum.shapes import MSO_SHAPE
shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
shp.name = "Card_1_Container"

# Fill
shp.fill.solid()
shp.fill.fore_color.rgb = RGBColor(0x1E, 0x27, 0x61)

# No outline
shp.line.fill.background()
# or: shp.line.color.rgb = RGBColor(...); shp.line.width = Pt(1)

# Corner radius: the `adjustments` array on ROUNDED_RECTANGLE holds one value in [0, 0.5]
# meaning the radius as a fraction of the shorter side. 0.1 ≈ subtle, 0.25 ≈ very rounded.
shp.adjustments[0] = 0.1
```

### 4b. Text box

```python
tb = slide.shapes.add_textbox(x, y, w, h)
tb.name = "Card_1_Title"

tf = tb.text_frame
tf.word_wrap = True

# IMPORTANT: default insets add padding; set to 0 when aligning with shape edges
tf.margin_left = Emu(0)
tf.margin_right = Emu(0)
tf.margin_top = Emu(0)
tf.margin_bottom = Emu(0)

# Vertical anchor (text inside the text frame)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE  # TOP | MIDDLE | BOTTOM

# First paragraph already exists; subsequent ones via add_paragraph()
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
run = p.add_run()
run.text = "Market Size"
run.font.name = "DM Sans"
run.font.size = Pt(18)
run.font.bold = True
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

### 4c. Text with colored text inside a shape

Set text on the shape's `text_frame` directly — no separate text box needed. Same API as above.

### 4d. Line / connector

```python
from pptx.enum.shapes import MSO_CONNECTOR
ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
ln.name = "Divider_Header"
ln.line.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
ln.line.width = Pt(0.75)
```

### 4e. Picture

```python
pic = slide.shapes.add_picture(path, x, y, width=w, height=h)  # height optional — auto-scales
pic.name = "Hero_Image"
```

### 4f. Table

```python
rows, cols = 3, 4
tbl_shape = slide.shapes.add_table(rows, cols, x, y, w, h)
tbl_shape.name = "ComparisonTable_Main"
tbl = tbl_shape.table
tbl.cell(0, 0).text = "Metric"
# …
```

Style per-cell: `cell.fill`, `cell.text_frame.paragraphs[0]` etc.

### 4g. Chart

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION

data = CategoryChartData()
data.categories = ["Q1", "Q2", "Q3", "Q4"]
data.add_series("Revenue", (12.3, 15.1, 17.8, 21.4))

chart_shape = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, w, h, data
)
chart_shape.name = "RevenueChart_Quarterly"
chart = chart_shape.chart
```

#### Better-looking charts

Default python-pptx charts look dated (heavy axis lines, default Office colors). Apply these to bring them in line with a styled deck:

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt
from pptx.enum.chart import XL_LEGEND_POSITION, XL_LABEL_POSITION

# Legend off for single series; right-side for multi-series
chart.has_legend = False
# chart.has_legend = True
# chart.legend.position = XL_LEGEND_POSITION.RIGHT
# chart.legend.include_in_layout = False

# Series color (palette accent)
plot = chart.plots[0]
for series in plot.series:
    fill = series.format.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string("0D9488")
    series.format.line.fill.background()  # no outline

# Data labels on bars
plot.has_data_labels = True
labels = plot.data_labels
labels.position = XL_LABEL_POSITION.OUTSIDE_END
labels.font.size = Pt(10)
labels.font.color.rgb = RGBColor.from_string("1E293B")

# Muted axis labels, no gridlines
for axis in (chart.category_axis, chart.value_axis):
    axis.tick_labels.font.size = Pt(10)
    axis.tick_labels.font.color.rgb = RGBColor.from_string("64748B")
    axis.format.line.fill.background()
chart.value_axis.major_gridlines.format.line.color.rgb = RGBColor.from_string("E2E8F0")
chart.category_axis.major_gridlines.format.line.fill.background()
```

For multi-series charts, iterate `plot.series` and assign one palette color per series. Keep the chart palette in sync with the spec's palette — random Office colors break the deck's design language.

#### Chart types

| Chart | `XL_CHART_TYPE` |
|---|---|
| Bar / column | `COLUMN_CLUSTERED`, `BAR_CLUSTERED`, `COLUMN_STACKED` |
| Line | `LINE`, `LINE_MARKERS` |
| Pie / doughnut | `PIE`, `DOUGHNUT` |
| Area | `AREA`, `AREA_STACKED` |
| Scatter | `XY_SCATTER`, `XY_SCATTER_LINES` |

`python-pptx` does NOT support gradient fills on chart elements via the API — drop to XML or pre-render the chart as an image (matplotlib → PNG → `add_picture`) for that.

---

## 5. Coordinate discipline

python-pptx does NOT compute layouts for you. If the spec says "three cards in a row, equal gaps", you compute it:

```python
MARGIN_X = Inches(0.5)
GAP = Inches(0.3)
USABLE_W = prs.slide_width - 2 * MARGIN_X
CARD_W = (USABLE_W - 2 * GAP) // 3  # integer EMU, no float drift
CARD_Y = Inches(2.0)
CARD_H = Inches(3.0)

for i, (title, body) in enumerate(cards):
    x = MARGIN_X + i * (CARD_W + GAP)
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, CARD_Y, CARD_W, CARD_H)
    shp.name = f"Card_{i+1}_Container"
    # … add child text boxes at x+inset, CARD_Y+inset …
```

Rules to avoid alignment drift:
- Compute each row's `top_y` ONCE and reuse it across every shape on that row. Never recompute per-shape.
- Use integer EMU arithmetic (`//` not `/`). Floats introduce sub-EMU drift that `measure.py` flags.
- When centering child B in parent A: `child_x = parent_x + (parent_w - child_w) // 2`. Do not eyeball.
- When two text boxes should share a center line, either give them the same `y` and `h` with the same vertical anchor, or compute `y` so `y + h/2` is identical for both.

---

## 6. Common python-pptx pitfalls

### 6a. Text frame padding

The default insets are **non-zero**. A text box of height 0.5" has ~0.1" eaten by top+bottom padding. If you place two text boxes with the same `y` and `h` but one has default padding and the other has 0 padding, their visual centers differ by ~0.05" and `measure.py` will call it out.

**Fix**: either set all four margins to `Emu(0)` everywhere and compensate by adding your own padding in the layout math, or pick one padding value and stick to it.

### 6b. Vertical anchor

`MSO_ANCHOR.MIDDLE` centers text within the text frame vertically — so if your text frame is taller than the text, the text visually sits in the middle. This is almost always what you want for labels inside cards. Default is `TOP`, which is almost never what you want.

### 6c. `auto_size` and word wrap

```python
tf.word_wrap = True   # wrap at the text frame's width
```

Do NOT rely on `tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_SHAPE` — it changes the shape's geometry behind your back, and `measure.py` will then report geometry that differs from what you set. Turn auto_size OFF and size text frames explicitly.

### 6d. Font availability

If the font name you set is not installed on the system that opens the file, PowerPoint substitutes. If the deck is viewed inside Databricks (rendered to PDF on the cluster), the cluster's installed fonts are what matter. See `style.md` for safer font choices.

To embed a font (advanced, XML-level):

```python
from pptx.oxml.ns import qn
# Add <p:embeddedFont> entries to prs.part.element — see python-pptx docs for the full dance.
```

For most decks, sticking to widely available fonts (Inter, DM Sans, Arial, Calibri, Georgia) is simpler.

### 6e. Smart quotes

When you set `run.text = 'the "Agreement"'`, PowerPoint displays straight ASCII quotes. For typographically correct quotes, write `"the \u201cAgreement\u201d"` (U+201C / U+201D).

### 6f. Color

Use `RGBColor(r, g, b)` — bytes, not floats:

```python
RGBColor(0x1E, 0x27, 0x61)  # correct
RGBColor(0.12, 0.15, 0.38)  # WRONG
```

Accept palette hex codes from `spec.md` and convert with `RGBColor.from_string("1E2761")`.

### 6g. Rounded parent + accent bar = corner overlap

Putting a thin rectangular accent bar on top of a `ROUNDED_RECTANGLE` parent looks fine in your math but the rectangular bar pokes through the parent's rounded corner — `invariants.py` and `measure.py` will both flag it (`any_corner_overlap: True`).

Two clean fixes:

```python
# Option A: parent is RECTANGLE, accent bar fits flush
parent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
bar    = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.08), h)

# Option B: parent stays ROUNDED, bar inset by the corner radius
radius = int(min(w, h) * 0.1)  # matches parent.adjustments[0] = 0.1
bar    = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y + radius, Inches(0.08), h - 2 * radius)
```

Do NOT silently accept the overlap — the design intent on a rounded card is clean corners.

### 6h. Image aspect ratio + sizing

`add_picture(path, x, y, width=w)` auto-scales height by aspect ratio (omit `height`). To do "contain" / "cover" math yourself:

```python
from PIL import Image as PILImage
src_w, src_h = PILImage.open(path).size
target_w, target_h = Inches(4), Inches(3)
# contain: fit inside, preserve ratio
scale = min(target_w / src_w, target_h / src_h)
draw_w = int(src_w * scale)
draw_h = int(src_h * scale)
draw_x = x + (target_w - draw_w) // 2
draw_y = y + (target_h - draw_h) // 2
slide.shapes.add_picture(path, draw_x, draw_y, draw_w, draw_h).name = "Hero_Image"
```

For "cover" (fill area, may crop), swap `min` for `max` and clip via the picture's `crop_left/right/top/bottom` properties.

### 6i. Slide masters and placeholders

If you build every slide from `slide_layouts[6]` (blank), you do not need masters. If you want a consistent header/footer across all slides, define it once in a master:

```python
master = prs.slide_master
# add shapes to master.shapes — they appear on every slide that uses a layout from this master
```

Most decks built by this skill use the blank layout and place every shape explicitly — it removes ambiguity about geometry, and the reviewer's measurements correspond 1:1 with what the generator wrote. Use masters only when the deck is large (10+ slides) and the header/footer truly never changes.

### 6k. Group shapes

python-pptx's support for creating new group shapes is limited. For the skill's purposes, **do not use groups**. Instead, rely on the naming convention (`Card_1_Container`, `Card_1_Title`, `Card_1_Body`) — `measure.py` uses prefix-matching to detect parent/child relationships.

---

## 7. File structure of the generator `.py`

Keep the generator file tidy and re-runnable:

```python
"""Build <deck>.pptx from <deck>.spec.md.

Re-runnable: safe to delete the output and re-run the whole script.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ---- Palette (from spec.md) -------------------------------------------------
PRIMARY   = RGBColor.from_string("0B2545")
SECONDARY = RGBColor.from_string("E6F1FF")
ACCENT    = RGBColor.from_string("FF3621")
INK       = RGBColor.from_string("111827")

# ---- Fonts (from spec.md) ---------------------------------------------------
HEADER_FONT = "DM Sans"
BODY_FONT   = "Inter"

# ---- Layout constants -------------------------------------------------------
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN  = Inches(0.5)
GAP     = Inches(0.3)

def build_slide_1(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # ... one block of code per slide, with comments only where the WHY is non-obvious.

def main(out_path):
    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H
    build_slide_1(prs)
    build_slide_2(prs)
    # ...
    prs.save(out_path)
    print(f"Saved {out_path}")

if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/out.pptx")
```

One `build_slide_N` per slide. No "v2" copies of functions. No dead code.

---

## 8. Self-check commands

After the generator runs, before handing off:

```python
!python -m markitdown /Volumes/.../deck.pptx | head -80
!python scripts/measure.py /Volumes/.../deck.pptx > /tmp/measure.txt
!python scripts/invariants.py /Volumes/.../deck.pptx > /tmp/inv.txt
```

- If markitdown shows missing content → fix and rebuild.
- If measure.py prints `Shape N` / `TextBox N` instead of your semantic names → you missed `.name =` somewhere; fix.
- If a contract from spec.md is obviously violated → fix.
- If invariants.py reports a cross-group overlap not listed in spec's "Overlap exceptions" → fix.

Do NOT judge subtle issues yourself — that is the reviewer's job. But do not hand off a clearly broken deck either.
