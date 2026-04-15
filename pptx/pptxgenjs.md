# PptxGenJS Tutorial

## Shape Naming (REQUIRED)

**Every `addShape`, `addText`, `addImage`, `addTable` call MUST include `objectName`.**

Anonymous shapes become `Shape 3`, `Shape 15`, `Text 26` in `measure.py` output — the reviewer cannot map numbers back to design intent, and the whole generator/evaluator loop breaks. A deck with anonymous shapes is auto-FAILed by the reviewer and must be rebuilt.

**Pattern**: `<Section>_<Purpose>_<Role>`

- **Section**: `Header`, `Footer`, `ComponentCard`, `StatCard`, `Timeline`, `ComparisonTable`, `TitleBlock`, `SideBar`, `Legend`
- **Purpose**: the specific instance — `LLMCore`, `MarketSize`, `Row3`, `Risk1`, or a 1-based index if the instance is generic (`Card1`, `Card2`)
- **Role**: what the shape IS — `Container`, `Title`, `Value`, `Label`, `Badge`, `AccentBar`, `Icon`, `Description`, `Separator`, `Background`

```js
// ✅ GOOD — semantic, maps to design intent
s.addShape(pres.shapes.RECTANGLE, {
  objectName: "StatCard_MarketSize_Container",
  x: 0.65, y: 4.2, w: 1.7, h: 0.72, fill: { color: C.navy },
});
s.addText("$47B", {
  objectName: "StatCard_MarketSize_Value",
  x: 0.65, y: 4.25, w: 1.7, h: 0.35,
  fontSize: 20, bold: true, color: C.gold,
  align: "center", valign: "middle", margin: 0,
});
s.addText("Market Size 2024", {
  objectName: "StatCard_MarketSize_Label",
  x: 0.65, y: 4.60, w: 1.7, h: 0.27,
  fontSize: 9, color: C.muted,
  align: "center", valign: "middle", margin: 0,
});

// ❌ BAD — anonymous, measure.py emits "Shape 3" / "Text 26"
s.addShape(pres.shapes.RECTANGLE, { x: 0.65, y: 4.2, w: 1.7, h: 0.72, ... });
s.addText("$47B", { x: 0.65, y: 4.22, w: 1.7, h: 0.32, ... });
```

**Conventions**:
- Use underscores, not hyphens (so names are valid XML identifiers and easy to grep).
- Keep under ~50 chars; measure.py truncates long names.
- Match the name used in `<deck>.spec.md` alignment contracts exactly — the reviewer does a text match.
- For repeated elements (e.g. 6 component cards), use numeric suffix: `ComponentCard_1_Title`, `ComponentCard_2_Title`, …

---

## Setup & Basic Structure

```javascript
const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';  // or 'LAYOUT_16x10', 'LAYOUT_4x3', 'LAYOUT_WIDE'
pres.author = 'Your Name';
pres.title = 'Presentation Title';

let slide = pres.addSlide();
slide.addText("Hello World!", { x: 0.5, y: 0.5, fontSize: 36, color: "363636" });

pres.writeFile({ fileName: "Presentation.pptx" });
```

## Layout Dimensions

Slide dimensions (coordinates in inches):
- `LAYOUT_16x9`: 10" × 5.625" (default)
- `LAYOUT_16x10`: 10" × 6.25"
- `LAYOUT_4x3`: 10" × 7.5"
- `LAYOUT_WIDE`: 13.3" × 7.5"

---

## Text & Formatting

```javascript
// Basic text
slide.addText("Simple Text", {
  x: 1, y: 1, w: 8, h: 2, fontSize: 24, fontFace: "Arial",
  color: "363636", bold: true, align: "center", valign: "middle"
});

// Character spacing (use charSpacing, not letterSpacing which is silently ignored)
slide.addText("SPACED TEXT", { x: 1, y: 1, w: 8, h: 1, charSpacing: 6 });

// Rich text arrays
slide.addText([
  { text: "Bold ", options: { bold: true } },
  { text: "Italic ", options: { italic: true } }
], { x: 1, y: 3, w: 8, h: 1 });

// Multi-line text (requires breakLine: true)
slide.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2", options: { breakLine: true } },
  { text: "Line 3" }  // Last item doesn't need breakLine
], { x: 0.5, y: 0.5, w: 8, h: 2 });

// Text box margin (internal padding)
slide.addText("Title", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  margin: 0  // Use 0 when aligning text with other elements like shapes or icons
});
```

**Tip:** Text boxes have internal margin by default. Set `margin: 0` when you need text to align precisely with shapes, lines, or icons at the same x-position.

---

## Lists & Bullets

```javascript
// ✅ CORRECT: Multiple bullets
slide.addText([
  { text: "First item", options: { bullet: true, breakLine: true } },
  { text: "Second item", options: { bullet: true, breakLine: true } },
  { text: "Third item", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });

// ❌ WRONG: Never use unicode bullets
slide.addText("• First item", { ... });  // Creates double bullets

// Sub-items and numbered lists
{ text: "Sub-item", options: { bullet: true, indentLevel: 1 } }
{ text: "First", options: { bullet: { type: "number" }, breakLine: true } }
```

---

## Shapes

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 1.5, h: 3.0,
  fill: { color: "FF0000" }, line: { color: "000000", width: 2 }
});

slide.addShape(pres.shapes.OVAL, { x: 4, y: 1, w: 2, h: 2, fill: { color: "0000FF" } });

slide.addShape(pres.shapes.LINE, {
  x: 1, y: 3, w: 5, h: 0, line: { color: "FF0000", width: 3, dashType: "dash" }
});

// With transparency
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "0088CC", transparency: 50 }
});

// Rounded rectangle (rectRadius only works with ROUNDED_RECTANGLE, not RECTANGLE)
// ⚠️ Don't pair with rectangular accent overlays — they won't cover rounded corners. Use RECTANGLE instead.
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" }, rectRadius: 0.1
});

// With shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 }
});
```

Shadow options:

| Property | Type | Range | Notes |
|----------|------|-------|-------|
| `type` | string | `"outer"`, `"inner"` | |
| `color` | string | 6-char hex (e.g. `"000000"`) | No `#` prefix, no 8-char hex — see Common Pitfalls |
| `blur` | number | 0-100 pt | |
| `offset` | number | 0-200 pt | **Must be non-negative** — negative values corrupt the file |
| `angle` | number | 0-359 degrees | Direction the shadow falls (135 = bottom-right, 270 = upward) |
| `opacity` | number | 0.0-1.0 | Use this for transparency, never encode in color string |

To cast a shadow upward (e.g. on a footer bar), use `angle: 270` with a positive offset — do **not** use a negative offset.

**Note**: Gradient fills are not natively supported. Use a gradient image as a background instead.

---

## Images

### Image Sources

```javascript
// From file path
slide.addImage({ path: "images/chart.png", x: 1, y: 1, w: 5, h: 3 });

// From URL
slide.addImage({ path: "https://example.com/image.jpg", x: 1, y: 1, w: 5, h: 3 });

// From base64 (faster, no file I/O)
slide.addImage({ data: "image/png;base64,iVBORw0KGgo...", x: 1, y: 1, w: 5, h: 3 });
```

### Image Options

```javascript
slide.addImage({
  path: "image.png",
  x: 1, y: 1, w: 5, h: 3,
  rotate: 45,              // 0-359 degrees
  rounding: true,          // Circular crop
  transparency: 50,        // 0-100
  flipH: true,             // Horizontal flip
  flipV: false,            // Vertical flip
  altText: "Description",  // Accessibility
  hyperlink: { url: "https://example.com" }
});
```

### Image Sizing Modes

```javascript
// Contain - fit inside, preserve ratio
{ sizing: { type: 'contain', w: 4, h: 3 } }

// Cover - fill area, preserve ratio (may crop)
{ sizing: { type: 'cover', w: 4, h: 3 } }

// Crop - cut specific portion
{ sizing: { type: 'crop', x: 0.5, y: 0.5, w: 2, h: 2 } }
```

### Calculate Dimensions (preserve aspect ratio)

```javascript
const origWidth = 1978, origHeight = 923, maxHeight = 3.0;
const calcWidth = maxHeight * (origWidth / origHeight);
const centerX = (10 - calcWidth) / 2;

slide.addImage({ path: "image.png", x: centerX, y: 1.2, w: calcWidth, h: maxHeight });
```

### Supported Formats

- **Standard**: PNG, JPG, GIF (animated GIFs work in Microsoft 365)
- **SVG**: Works in modern PowerPoint/Microsoft 365

---

## Icons

Use react-icons to generate SVG icons, then rasterize to PNG for universal compatibility.

### Setup

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaCheckCircle, FaChartLine } = require("react-icons/fa");

function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}
```

### Add Icon to Slide

```javascript
const iconData = await iconToBase64Png(FaCheckCircle, "#4472C4", 256);

slide.addImage({
  data: iconData,
  x: 1, y: 1, w: 0.5, h: 0.5  // Size in inches
});
```

**Note**: Use size 256 or higher for crisp icons. The size parameter controls the rasterization resolution, not the display size on the slide (which is set by `w` and `h` in inches).

### Icon Libraries

Install: `npm install -g react-icons react react-dom sharp`

Popular icon sets in react-icons:
- `react-icons/fa` - Font Awesome
- `react-icons/md` - Material Design
- `react-icons/hi` - Heroicons
- `react-icons/bi` - Bootstrap Icons

---

## Slide Backgrounds

```javascript
// Solid color
slide.background = { color: "F1F1F1" };

// Color with transparency
slide.background = { color: "FF3399", transparency: 50 };

// Image from URL
slide.background = { path: "https://example.com/bg.jpg" };

// Image from base64
slide.background = { data: "image/png;base64,iVBORw0KGgo..." };
```

---

## Tables

```javascript
slide.addTable([
  ["Header 1", "Header 2"],
  ["Cell 1", "Cell 2"]
], {
  x: 1, y: 1, w: 8, h: 2,
  border: { pt: 1, color: "999999" }, fill: { color: "F1F1F1" }
});

// Advanced with merged cells
let tableData = [
  [{ text: "Header", options: { fill: { color: "6699CC" }, color: "FFFFFF", bold: true } }, "Cell"],
  [{ text: "Merged", options: { colspan: 2 } }]
];
slide.addTable(tableData, { x: 1, y: 3.5, w: 8, colW: [4, 4] });
```

---

## Charts

```javascript
// Bar chart
slide.addChart(pres.charts.BAR, [{
  name: "Sales", labels: ["Q1", "Q2", "Q3", "Q4"], values: [4500, 5500, 6200, 7100]
}], {
  x: 0.5, y: 0.6, w: 6, h: 3, barDir: 'col',
  showTitle: true, title: 'Quarterly Sales'
});

// Line chart
slide.addChart(pres.charts.LINE, [{
  name: "Temp", labels: ["Jan", "Feb", "Mar"], values: [32, 35, 42]
}], { x: 0.5, y: 4, w: 6, h: 3, lineSize: 3, lineSmooth: true });

// Pie chart
slide.addChart(pres.charts.PIE, [{
  name: "Share", labels: ["A", "B", "Other"], values: [35, 45, 20]
}], { x: 7, y: 1, w: 5, h: 4, showPercent: true });
```

### Better-Looking Charts

Default charts look dated. Apply these options for a modern, clean appearance:

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",

  // Custom colors (match your presentation palette)
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],

  // Clean background
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },

  // Muted axis labels
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",

  // Subtle grid (value axis only)
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },

  // Data labels on bars
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "1E293B",

  // Hide legend for single series
  showLegend: false,
});
```

**Key styling options:**
- `chartColors: [...]` - hex colors for series/segments
- `chartArea: { fill, border, roundedCorners }` - chart background
- `catGridLine/valGridLine: { color, style, size }` - grid lines (`style: "none"` to hide)
- `lineSmooth: true` - curved lines (line charts)
- `legendPos: "r"` - legend position: "b", "t", "l", "r", "tr"

---

## Slide Masters

```javascript
pres.defineSlideMaster({
  title: 'TITLE_SLIDE', background: { color: '283A5E' },
  objects: [{
    placeholder: { options: { name: 'title', type: 'title', x: 1, y: 2, w: 8, h: 2 } }
  }]
});

let titleSlide = pres.addSlide({ masterName: "TITLE_SLIDE" });
titleSlide.addText("My Title", { placeholder: "title" });
```

---

## After `writeFile` — Hand off to the reviewer

**If you are the `pptx-content-creator` agent**: after `writeFile`, run `markitdown` + `measure.py` for your own sanity (fix obvious bugs), write `<deck>.spec.md`, then return to the orchestrator. The orchestrator will dispatch `pptx-slide-reviewer` in a fresh subagent to grade. You never self-approve. See [agents/content-creator.md](agents/content-creator.md).

**If you are working without the agent split** (discouraged — re-read SKILL.md's three-agent workflow first): the verification checklist below is the minimum you owe the user. You are biased-generous about your own work; the reviewer agent exists precisely because this checklist is hard to run honestly on yourself.

---

## Verification checklist (minimum; reviewer agent enforces this harder)

**Generating the file is not the end of the task.** PptxGenJS will happily emit silently misaligned slides: a 0.03" off-center icon, a title whose middle doesn't match a badge in the same header band, cards whose inner elements drift by a few hundredths of an inch. These are invisible when you're staring at your own coordinate arithmetic but obvious on the rendered slide.

Run the full verification loop before declaring the task done:

```bash
python scripts/measure.py output.pptx          # numeric alignment check
# then: render JPGs and do visual QA — see SKILL.md "Converting to Images" and "QA"
```

### measure.py is not a checkbox — it is a READ step

Running `measure.py` and immediately moving on is the most common failure mode of this skill. The tool prints a lot of numbers; if you don't actually parse them, you have done nothing. **Piping to `head -60` and calling it done is not verification.** Either read the full report, or grep for the signals below.

**Required: slide-by-slide, shape-by-shape review.** Run per-slide and read each in full:

```bash
python3 scripts/measure.py output.pptx --slide 1 > /tmp/s1.txt
python3 scripts/measure.py output.pptx --slide 2 > /tmp/s2.txt
# etc.
```

For every slide, inspect every shape. For each shape write a one-line verdict in your reply before moving on:

- **`children_alignment` → `padding_aware dx/dy`** — for every text/content child: "should this be centered in parent?" If yes and delta ≠ 0 → bug. If no → state why not.
- **`candidate_row_pairs` → `cY_delta`** — "did I intend these to share a horizontal centerline?" Ignore full-height decorative bars. For all content pairs: 0 = correct, non-zero = fix.
- **`candidate_column_pairs` → `cX_delta`** — same for vertical centerlines.
- **Key sibling pairs you designed** (title + badge, number + caption, icon + label) — look them up explicitly in siblings and confirm `cY` or `cX` = 0.

**Write the verdict per shape, per slide, in your reply.** "All intentional" with no per-shape explanation is not accepted. No verdict = no verification.

**"measure.py ran with no structural errors" is NOT verification.** The tool almost never errors; its job is to surface numbers, and your job is to read them. A clean build that prints 200 lines of alignment data you never looked at is indistinguishable from a broken build.

**Do not declare the task complete on the strength of `writeFile` alone**, even when the environment lacks LibreOffice/poppler for visual QA. `measure.py` runs with only Python — it is always available and its output is always actionable. Run it, read it, fix what it flags, rebuild, re-run. Only then report back.

**Reading measure.py output for pptxgenjs-generated decks** — focus on these signals:

- **Sibling `cX` / `cY` deltas in the tens of thousands of EMU** (1000 EMU ≈ 0.001") almost always mean you *intended* to center two elements on the same axis but the math was off. Examples that bit this skill in testing:
  - Icon circle at `y: card.y + 0.18, h: 0.4` (center_y = card.y + 0.38) paired with title at `y: card.y + 0.15, h: 0.4, valign: "middle"` (center_y = card.y + 0.35) → sibling `cY = -27432` across every card.
  - Header-band title with `valign: "middle"` + h=0.5 (center = band_center) paired with a slide-number label using default top-anchor + smaller h (center ≠ band_center) → sibling `cY = ±45720`.
  - Fix: make the two boxes either share the same `y + h/2`, or give both `valign: "middle"` inside boxes that share `y` and `h`.

- **`padding_aware center_delta` non-zero on a child inside a container** — the child is not centered in its parent. Small dx/dy (under ~50000 EMU) is almost always a bug unless the layout is explicitly asymmetric.

- **`parent_roundrect_corners.any_corner_overlap: True`** — an accent bar / side border is poking into the parent's rounded corner. Either swap the parent for `RECTANGLE` (see pitfall 8 below) or shrink the bar.

Fix, rebuild, re-measure. A clean `measure.py` pass is the gate to visual QA, not a substitute for it.

---

## Common Pitfalls

⚠️ These issues cause file corruption, visual bugs, or broken output. Avoid them.

1. **NEVER use "#" with hex colors** - causes file corruption
   ```javascript
   color: "FF0000"      // ✅ CORRECT
   color: "#FF0000"     // ❌ WRONG
   ```

2. **NEVER encode opacity in hex color strings** - 8-char colors (e.g., `"00000020"`) corrupt the file. Use the `opacity` property instead.
   ```javascript
   shadow: { type: "outer", blur: 6, offset: 2, color: "00000020" }          // ❌ CORRUPTS FILE
   shadow: { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.12 }  // ✅ CORRECT
   ```

3. **Use `bullet: true`** - NEVER unicode symbols like "•" (creates double bullets)

4. **Use `breakLine: true`** between array items or text runs together

5. **Avoid `lineSpacing` with bullets** - causes excessive gaps; use `paraSpaceAfter` instead

6. **Each presentation needs fresh instance** - don't reuse `pptxgen()` objects

7. **NEVER reuse option objects across calls** - PptxGenJS mutates objects in-place (e.g. converting shadow values to EMU). Sharing one object between multiple calls corrupts the second shape.
   ```javascript
   const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });  // ❌ second call gets already-converted values
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });

   const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });  // ✅ fresh object each time
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   ```

8. **Don't use `ROUNDED_RECTANGLE` with accent borders** - rectangular overlay bars won't cover rounded corners. Use `RECTANGLE` instead.
   ```javascript
   // ❌ WRONG: Accent bar doesn't cover rounded corners
   slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1, y: 1, w: 3, h: 1.5, fill: { color: "FFFFFF" } });
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 0.08, h: 1.5, fill: { color: "0891B2" } });

   // ✅ CORRECT: Use RECTANGLE for clean alignment
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 3, h: 1.5, fill: { color: "FFFFFF" } });
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 0.08, h: 1.5, fill: { color: "0891B2" } });
   ```

---

## Quick Reference

- **Shapes**: RECTANGLE, OVAL, LINE, ROUNDED_RECTANGLE
- **Charts**: BAR, LINE, PIE, DOUGHNUT, SCATTER, BUBBLE, RADAR
- **Layouts**: LAYOUT_16x9 (10"×5.625"), LAYOUT_16x10, LAYOUT_4x3, LAYOUT_WIDE
- **Alignment**: "left", "center", "right"
- **Chart data labels**: "outEnd", "inEnd", "center"
