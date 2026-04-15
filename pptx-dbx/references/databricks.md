# Databricks Notebook Environment Guide

This skill runs inside a Databricks Notebook — typically invoked by **Genie Code** or a similar notebook-based agent. The environment differs meaningfully from a laptop shell, and the choices you make here (where files live, how packages get installed, how renders happen) determine whether the user can actually download the finished deck.

Read this before starting any task.

---

## 1. Compute types — what matters

Databricks has a few compute flavors, and your toolchain options differ across them:

| Compute | `%pip install` | `%sh apt-get` / system packages | Arbitrary binaries (LibreOffice, poppler) |
|---|---|---|---|
| **Classic all-purpose cluster** (with shell access) | ✅ | ✅ (sudo available in `%sh`) | ✅ (install once, persists for cluster life) |
| **Classic job cluster** | ✅ | ✅ but you must re-install every run (init script recommended) | ✅ via init script |
| **Serverless notebooks / Serverless compute** | ✅ | ❌ (no sudo, `%sh` is sandboxed) | ❌ |
| **SQL Warehouse** | n/a | n/a | n/a — do not run this skill there |

**Rule of thumb**: if `%sh apt-get install libreoffice` fails, you are on serverless. Fall back to the Aspose.Slides PDF route (see §5) or skip visual QA entirely.

---

## 2. Installing Python packages

Always install in one cell, then restart Python in the next cell. If you try to `import python-pptx` in the same cell as `%pip install`, it will not find the freshly installed package.

```python
%pip install python-pptx "markitdown[pptx]" Pillow defusedxml
# optional, only if doing visual QA without LibreOffice:
%pip install aspose-slides
```

```python
dbutils.library.restartPython()
```

After restart, imports work normally:

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
```

**Do not** `!pip install` — that installs into the driver shell, not the notebook's Python kernel, and you will get ModuleNotFoundError.

---

## 3. Where to put files

Databricks has several filesystem locations. Pick the right one:

| Location | Path example | Good for | Survives cluster restart? | User can download? |
|---|---|---|---|---|
| **Unity Catalog Volume** | `/Volumes/<catalog>/<schema>/<volume>/deck.pptx` | final deliverables | ✅ | ✅ (UI download, or `display(fileUrl)`) |
| **Workspace file** | `/Workspace/Users/<email>/decks/deck.pptx` | final deliverables, small assets | ✅ | ✅ |
| **DBFS (legacy)** | `/dbfs/FileStore/decks/deck.pptx` | legacy; works but not recommended on new workspaces | ✅ | ✅ |
| **Driver local tmp** | `/tmp/deck.pptx` | scratch, intermediate files | ❌ (gone on detach) | ❌ |
| **Local notebook CWD** | `./deck.pptx` | **DO NOT** — writes to a non-persistent driver path | ❌ | ❌ |

**Strong preference**: write final outputs to a **Volume**. Volumes are the modern, Unity-Catalog-governed location. Use `/tmp/` only for scratch (unpacked XML, measure.py reports, intermediate PDFs).

### Discovering the right Volume path

If the user has not said where to put the deck, ask — or check `dbutils.fs.ls("/Volumes/")` to list catalogs the agent can see, then propose a path and confirm before writing. Do not silently write to a random location.

If no Volume is available, fall back to a Workspace file under the user's home:

```python
import os
user = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()
out_dir = f"/Workspace/Users/{user}/pptx-out"
os.makedirs(out_dir, exist_ok=True)
```

---

## 4. Running shell commands

The skill's scripts (`measure.py`, `invariants.py`, etc.) are pure Python and can be invoked either way:

```python
# Option A: subprocess (works everywhere)
import subprocess
r = subprocess.run(
    ["python", "/Workspace/.../pptx-dbx/scripts/measure.py", "/Volumes/.../deck.pptx", "--slide", "1"],
    capture_output=True, text=True,
)
print(r.stdout)

# Option B: ! magic (only works if the skill files are on the driver — see §7)
!python /path/to/measure.py /Volumes/.../deck.pptx --slide 1
```

For long outputs, redirect to a `/tmp/` file and `head`/`cat` in a separate cell — the notebook UI truncates cell outputs around 1 MB.

---

## 5. Rendering slides to images

Visual QA requires rendering slides. Three strategies depending on compute:

### 5a. Classic compute with shell access (preferred)

Install LibreOffice + poppler once per cluster:

```python
%sh
sudo apt-get update
sudo apt-get install -y libreoffice poppler-utils
```

Then convert and rasterize:

```python
!python /path/to/pptx-dbx/scripts/office/soffice.py --headless --convert-to pdf /Volumes/.../deck.pptx --outdir /tmp
!pdftoppm -jpeg -r 150 /tmp/deck.pdf /tmp/slide
!ls /tmp/slide-*.jpg
```

Display an image inline:

```python
from IPython.display import Image, display
display(Image("/tmp/slide-01.jpg"))
```

### 5b. Serverless / no shell access: Aspose.Slides

```python
%pip install aspose-slides
dbutils.library.restartPython()
```

```python
import aspose.slides as slides
with slides.Presentation("/Volumes/.../deck.pptx") as pres:
    pres.save("/tmp/deck.pdf", slides.export.SaveFormat.PDF)
```

Then either install `pdf2image` (pure Python, depends on poppler which may not be available) **or** use Aspose to render directly to PNG per slide:

```python
import aspose.slides as slides
with slides.Presentation("/Volumes/.../deck.pptx") as pres:
    for i, slide in enumerate(pres.slides, 1):
        img = slide.get_thumbnail(1.5, 1.5)  # zoom x1.5 ≈ 144 DPI
        img.save(f"/tmp/slide-{i:02d}.png", slides.ImageFormat.PNG)
```

**Caveat**: Aspose's free tier watermarks the first slide. This is acceptable for QA (you are inspecting layout, not distributing this PNG) but do NOT ship the Aspose-rendered PDF as a deliverable — always ship the original `.pptx` (and, if the user asked for PDF, use LibreOffice-produced PDF, never Aspose's watermarked one).

### 5c. No rendering available

Fall back to structural QA only. Run `measure.py` and `invariants.py`. In the final handoff to the user, state explicitly: *"Visual QA was skipped because the cluster does not have a rendering toolchain. Structural checks (geometry, overlaps, clearances) passed."*

---

## 6. Delivering files to the user

The deck lives on a Volume (or Workspace file). Hand it to the user with a clickable download link rendered via `displayHTML` — that is the primary delivery mechanism. Print the absolute path as a backup so the user has both the link and the path.

### 6a. The standard delivery cell

```python
out = "/Volumes/main/default/decks/quarterly_review.pptx"
print(f"Deck saved: {out}")

# Volume files: download via the Files API endpoint (authenticated by the user's browser session)
import urllib.parse
href = "/api/2.0/fs/files" + urllib.parse.quote(out)
displayHTML(f'<a href="{href}" download style="font-size:16px;font-weight:600">⬇️ Download {out.rsplit("/",1)[-1]}</a>')
```

The `/api/2.0/fs/files{path}` endpoint streams the Volume file. Because the user is signed into the workspace in the same browser, the link works for them — clicking it triggers a normal browser download. It does NOT require an access token in the URL.

For **Workspace files** (the fallback when no Volume is available), use the `/files/` route instead:

```python
import os
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
user = ctx.userName().get()
out = f"/Workspace/Users/{user}/pptx-out/quarterly_review.pptx"
os.makedirs(os.path.dirname(out), exist_ok=True)
# ...write file...
displayHTML(f'<a href="/files/Users/{user}/pptx-out/quarterly_review.pptx" download>⬇️ Download deck</a>')
```

(`/files/` works for Workspace files but NOT for Volumes — keep the two URL forms straight.)

### 6b. PDF deliverable

If the user asked for a PDF as well, render via LibreOffice (Aspose's free tier watermarks slide 1, which is unacceptable for delivery):

```python
!python /Workspace/Repos/<user>/pptx-dbx/scripts/office/soffice.py \
    --headless --convert-to pdf /Volumes/.../deck.pptx --outdir /Volumes/.../
```

Then emit a second `<a>` link for the PDF beside the pptx link.

### 6c. Hard rule

**Never leave the final file in `/tmp/`.** The driver `/tmp/` vanishes when the cluster detaches. Either save directly to the Volume / Workspace file or `dbutils.fs.cp("file:/tmp/deck.pptx", "/Volumes/...")` before emitting the download link. A download link pointing at `/tmp/` is broken the moment the cluster restarts.

### 6d. Catalog Explorer fallback

If `displayHTML` is suppressed (some Genie Code execution modes only render plain stdout), the user can still download from the Catalog Explorer UI:

> Catalog (left nav) → `<catalog>` → `<schema>` → Volumes → `<volume>` → select file → **Download**

Print this navigation hint as a backup so the user always has a path to the file:

```python
print("If the link above does not render, download via Catalog Explorer:")
print("  Catalog → main → default → decks → quarterly_review.pptx → Download")
```

---

## 7. Making the skill's scripts available

The scripts under `scripts/` need to be reachable from a notebook cell. Three patterns:

1. **Repo-backed**: clone this skill into a Databricks Repo (`/Workspace/Repos/<user>/pptx-dbx/`). Then `!python /Workspace/Repos/<user>/pptx-dbx/scripts/measure.py ...` just works.
2. **Volume-backed**: upload the skill folder to a Volume and invoke scripts from there.
3. **In-cell inlining**: copy the script contents into a cell. Works but loses updates when the skill is improved.

For Genie Code specifically, option 1 (Databricks Repo) is the cleanest because Genie already knows how to read files from Repos and can reference paths absolutely.

---

## 8. Notebook cell discipline

A few habits that avoid frustration:

- **One concern per cell.** Install in one cell, restart in another, import in a third, do work in the fourth. Mixing them causes ordering bugs.
- **Print absolute paths.** Every cell that writes a file should end with `print(path)` so downstream cells don't guess.
- **Clean up `/tmp/` between runs** if you are rebuilding the deck repeatedly — leftover `slide-01.jpg` from a prior run will mislead your visual QA.
- **Capture long subprocess outputs to `/tmp/` files**, then `head`/`tail` them in a follow-up cell. The notebook's cell-output size limit will truncate long measure.py reports.

---

## 9. Limits and gotchas specific to Genie Code

Genie Code autonomously writes and executes code cells. A few things to watch:

- Genie may place code in multiple cells; the skill's self-check loop (`measure` → fix → re-measure) relies on state across cells. Make sure each cell re-loads the pptx from disk rather than holding a stale in-memory `Presentation` object across edits.
- Genie usually has access to notebook magics (`%pip`, `%sh`) but its permission model may block `%sh apt-get`. If install commands fail with a permission error, that is the signal to fall back to Aspose.
- Genie's memory is not persistent across sessions — if the skill depends on a previously installed Aspose or LibreOffice, re-verify at the start of each session with a quick `import aspose.slides` or `!which soffice`.
