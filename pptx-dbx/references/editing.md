# Editing Existing Presentations (Databricks)

This covers two modes of editing:

1. **python-pptx mode** — open, modify, save. Best for content updates (replacing text, swapping images, changing colors) when the template's structure is already correct.
2. **XML unpack/pack mode** — unzip the .pptx, edit XML, repack. Necessary when the change is structural (adding/removing slides, re-ordering, deep formatting) or when python-pptx's API doesn't expose the attribute you need.

The tradeoff: python-pptx is faster and safer for 80% of edits; XML mode is the escape hatch when python-pptx cannot express the change.

---

## 1. python-pptx editing mode

```python
from pptx import Presentation
prs = Presentation("/Volumes/.../template.pptx")

for slide in prs.slides:
    for shp in slide.shapes:
        if shp.has_text_frame:
            for para in shp.text_frame.paragraphs:
                for run in para.runs:
                    if run.text.strip() == "REPLACE_ME_TITLE":
                        run.text = "Q4 Revenue Review"

prs.save("/Volumes/.../output.pptx")
```

**Key API**:
- `prs.slides` — iterable of slides
- `slide.shapes` — all shapes on the slide
- `shape.has_text_frame` / `shape.text_frame` — text access
- `text_frame.paragraphs[i].runs[j].text` — the actual string (preserves formatting)
- `shape.fill`, `shape.line`, `shape.name` — styling + identification

**Do not** set `text_frame.text = "..."` directly when you care about formatting — it collapses all runs into a single unformatted run. Always edit the existing `run.text` to preserve the template's font/color/size.

### Replacing placeholder images

```python
from pptx.util import Inches
for slide in prs.slides:
    for shp in slide.shapes:
        if shp.name == "HeroImage":
            # Can't replace image in place; remove + re-add
            left, top, w, h = shp.left, shp.top, shp.width, shp.height
            sp = shp._element
            sp.getparent().remove(sp)
            slide.shapes.add_picture("/Volumes/.../new.png", left, top, width=w, height=h).name = "HeroImage"
```

---

## 2. XML unpack/pack mode

When python-pptx can't express the edit — or the change is structural (delete slide 3, reorder, add a layout) — drop to XML.

### Workflow

1. **Analyze**:
   ```python
   !python scripts/thumbnail.py /Volumes/.../template.pptx
   !python -m markitdown /Volumes/.../template.pptx
   ```
   Review thumbnails for layouts, markitdown output for placeholder text.

2. **Plan slide mapping**: for each content section, pick a template slide.

   ⚠️ **USE VARIED LAYOUTS** — monotonous decks are a common failure mode. Don't default to basic title + bullet slides. Actively seek:
   - Multi-column layouts (2-column, 3-column)
   - Image + text combinations
   - Full-bleed images with text overlay
   - Quote / callout slides
   - Section dividers
   - Stat / number callouts
   - Icon grids or icon + text rows

   Match content type to layout style.

3. **Unpack**:
   ```python
   !python scripts/office/unpack.py /Volumes/.../template.pptx /tmp/unpacked/
   ```

4. **Structural changes** (do these before content edits):
   - Delete unwanted slides (remove from `<p:sldIdLst>`)
   - Duplicate slides to reuse (`add_slide.py`)
   - Reorder `<p:sldId>` elements in `ppt/presentation.xml`

5. **Edit content**: update text in each `slide{N}.xml`. If you have subagents, delegate per-slide edits in parallel. Tell each subagent:
   - Exact file path to edit
   - Use the Edit tool (not `sed`, not Python — Edit forces specificity)
   - The formatting rules below

6. **Clean**:
   ```python
   !python scripts/clean.py /tmp/unpacked/
   ```

7. **Pack**:
   ```python
   !python scripts/office/pack.py /tmp/unpacked/ /Volumes/.../output.pptx --original /Volumes/.../template.pptx
   ```

---

## 3. Scripts reference

| Script | Purpose |
|--------|---------|
| `unpack.py` | Extract and pretty-print PPTX |
| `add_slide.py` | Duplicate slide or create from layout |
| `clean.py` | Remove orphaned files |
| `pack.py` | Repack with validation |
| `thumbnail.py` | Create visual grid of slides |

### unpack.py
```
!python scripts/office/unpack.py input.pptx unpacked/
```
Extracts PPTX, pretty-prints XML, escapes smart quotes.

### add_slide.py
```
!python scripts/add_slide.py unpacked/ slide2.xml        # Duplicate slide
!python scripts/add_slide.py unpacked/ slideLayout2.xml  # From layout
```
Prints `<p:sldId>` to insert into `<p:sldIdLst>` at the desired position.

### clean.py
```
!python scripts/clean.py unpacked/
```
Removes slides not in `<p:sldIdLst>`, unreferenced media, orphaned rels.

### pack.py
```
!python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```
Validates, repairs, condenses XML, re-encodes smart quotes.

### thumbnail.py
```
!python scripts/thumbnail.py input.pptx [output_prefix] [--cols N]
```
Creates `thumbnails.jpg` with slide filenames as labels. **Requires Pillow + a rendering toolchain** (LibreOffice or Aspose — see databricks.md §5).

Use for template analysis only (choosing layouts). For visual QA, use `soffice` + `pdftoppm` (or Aspose) to create full-resolution individual slide images — see SKILL.md.

---

## 4. Slide operations (XML level)

Slide order lives in `ppt/presentation.xml` → `<p:sldIdLst>`.

- **Reorder**: rearrange `<p:sldId>` elements.
- **Delete**: remove `<p:sldId>`, then run `clean.py`.
- **Add**: use `add_slide.py`. Never manually copy slide files — the script handles notes references, `Content_Types.xml`, and rel IDs that manual copying misses.

---

## 5. Editing content (XML level)

### Formatting rules

- **Bold all headers, subheadings, and inline labels**: use `b="1"` on `<a:rPr>`. This covers:
  - Slide titles
  - Section headers within a slide
  - Inline labels ("Status:", "Description:") at the start of a line
- **Never use unicode bullets (•)**: use proper list formatting with `<a:buChar>` or `<a:buAutoNum>`.
- **Bullet consistency**: let bullets inherit from the layout. Only specify `<a:buChar>` or `<a:buNone>` when overriding.

---

## 6. Common pitfalls

### Template adaptation

When source content has fewer items than the template:
- **Remove excess elements entirely** (images, shapes, text boxes), don't just clear text.
- Check for orphaned visuals after clearing text.
- Run visual QA to catch mismatched counts.

When replacing text with different-length content:
- **Shorter replacements**: usually safe.
- **Longer replacements**: may overflow or wrap unexpectedly. Test with visual QA.
- Consider truncating or splitting content to fit the template.

**Template slots ≠ source items**: if template has 4 team-member cards but source has 3 people, delete the 4th card's entire group (image + text boxes), not just the text.

### Multi-item content

If source has multiple items, create separate `<a:p>` elements — never concatenate into one string.

**❌ WRONG** — all items in one paragraph:
```xml
<a:p>
  <a:r><a:rPr .../><a:t>Step 1: Do the first thing. Step 2: Do the second thing.</a:t></a:r>
</a:p>
```

**✅ CORRECT** — separate paragraphs with bold headers:
```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" b="1" .../><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3919"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="2799" .../><a:t>Do the first thing.</a:t></a:r>
</a:p>
```

Copy `<a:pPr>` from the original paragraph to preserve line spacing. Use `b="1"` on headers.

### Smart quotes

Handled automatically by unpack/pack. But the Edit tool converts smart quotes to ASCII. **When adding new text with quotes, use XML entities:**

```xml
<a:t>the &#x201C;Agreement&#x201D;</a:t>
```

| Character | Name | Unicode | XML Entity |
|-----------|------|---------|------------|
| `"` | Left double quote | U+201C | `&#x201C;` |
| `"` | Right double quote | U+201D | `&#x201D;` |
| `'` | Left single quote | U+2018 | `&#x2018;` |
| `'` | Right single quote | U+2019 | `&#x2019;` |

### Other

- **Whitespace**: use `xml:space="preserve"` on `<a:t>` with leading/trailing spaces.
- **XML parsing**: use `defusedxml.minidom`, not `xml.etree.ElementTree` (which corrupts namespaces).

---

## 7. Databricks specifics

- Always write outputs to a **Volume** or **Workspace file**, not `/tmp/` — see databricks.md §3.
- Unpacked XML lives in `/tmp/unpacked/` during the edit; this is scratch and fine to lose on cluster detach.
- When launching subagents for parallel slide-XML edits, tell each subagent the absolute path (e.g. `/tmp/unpacked/ppt/slides/slide3.xml`) — not relative paths, because Databricks subagent working directories vary.
