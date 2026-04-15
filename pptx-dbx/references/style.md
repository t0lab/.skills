# Style Reference — Palettes, Typography, Spacing, Motifs

This file is the **style library** for the skill. The content creator picks from it (or invents something in the same spirit) and records the choice in `spec.md`. The code generator reads the choice from `spec.md` — it does not look here directly, because `spec.md` is the single source of truth.

If none of the palettes below fit the topic, **invent one**. The point is that the palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.

---

## 1. Philosophy — before you pick anything

- **Pick a bold, content-informed color palette.** Generic blue is the default that says "I didn't think about this." Match the mood of the subject matter: earthy tones for sustainability, saturated warm tones for consumer/retail, deep navy/charcoal for finance/enterprise, muted pastels for healthcare, high-contrast neons for dev-tooling/crypto.
- **Dominance over equality.** One color should dominate (60–70% visual weight), with 1–2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast.** Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif.** Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders, a thin rule at the top of every content slide, an oversized number in the corner. Carry it across every slide. A motif that appears once is an accident; appearing 5+ times is a design.

---

## 2. Color palettes

Each palette lists primary / secondary / accent. Primary is the dominant surface color (≥50% of visual weight). Secondary is supporting shapes, cards, section backgrounds. Accent is reserved for call-outs, key numbers, the ONE thing you want the eye to land on.

### Canonical palettes

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

### Databricks / data-centric palettes

Decks built on top of Databricks often talk about data, warehouses, ML — a few palettes aligned to that visual territory:

| Theme | Primary | Secondary | Accent | Use when… |
|-------|---------|-----------|--------|-----------|
| **Delta Warehouse** | `0B2545` (deep navy) | `E6F1FF` (ice) | `FF3621` (Databricks red) | enterprise data decks, DLT / Unity Catalog pitches |
| **Lakehouse Dawn** | `1B1B3A` (midnight) | `F7C59F` (peach) | `EFE9AE` (cream-yellow) | ML/AI narrative decks that still need warmth |
| **Notebook Graphite** | `1E1E1E` (near-black) | `E8E8E8` (soft gray) | `00A972` (Databricks green) | technical deep-dives, product internals |
| **Genie Ink** | `111827` (ink) | `9CA3AF` (slate gray) | `F97316` (orange) | agent/assistant product decks, demos |
| **Pipeline Mint** | `0F766E` (pine) | `CCFBF1` (mint wash) | `F59E0B` (amber) | data-quality, observability, cost-savings stories |

### Rules for inventing a palette

If you roll your own:
1. Stay within 3–4 colors including any neutrals. More than that and the deck fragments.
2. Test contrast: body text must be WCAG AA on its background (4.5:1). Titles and large display text can be AA Large (3:1).
3. Pick an accent that is visually distinct from both primary and secondary — it has to win the eye when used sparingly.
4. Write the chosen hex codes in `spec.md`. The code generator does not guess.

---

## 3. Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

### Recommended pairings

| Header font | Body font | Vibe |
|-------------|-----------|------|
| Georgia | Calibri | editorial, long-read |
| Arial Black | Arial | punchy, startup |
| Calibri | Calibri Light | clean corporate |
| Cambria | Calibri | traditional enterprise |
| Trebuchet MS | Calibri | friendly, approachable |
| Impact | Arial | bold, headline-driven |
| Palatino | Garamond | classical, academic |
| Consolas | Calibri | technical, dev-oriented |

### Databricks / notebook-aware pairings

| Header font | Body font | Vibe |
|-------------|-----------|------|
| DM Sans | Inter | modern SaaS, Databricks product-site look |
| IBM Plex Sans | IBM Plex Sans | unified type system, technical but warm |
| Space Grotesk | Inter | AI/agent product decks |
| JetBrains Mono (labels only) | Inter (body) | code-adjacent, dev-tool decks |

**Note on font availability**: PowerPoint embeds font references, not the fonts themselves. If the target viewer does not have the font installed, it substitutes. Safe bets across platforms are Arial, Calibri, Georgia, Cambria, Trebuchet MS, Consolas, Impact. Anything else (DM Sans, Inter, Plex, Space Grotesk) should ideally be **embedded** via `python-pptx`'s font-embedding capability, or the generator should provide a `.ttf`/`.otf` path. If the deck will only be viewed inside Databricks (e.g. rendered to PDF and downloaded), less safe fonts are fine — PDF rendering on the cluster bakes in the glyphs.

### Sizes

| Element | Size |
|---------|------|
| Slide title | 36–44pt bold |
| Section header | 20–24pt bold |
| Body text | 14–16pt |
| Captions / footers | 10–12pt, muted |
| Display stat number | 60–96pt, bold, color=accent |

---

## 4. Spacing

- **0.5" minimum margins** from every slide edge. Anything tighter looks cramped and risks clipping when exported.
- **0.3–0.5" between content blocks.** Pick ONE gap value for a given deck and use it everywhere. Random gap values are the #1 reason a deck "feels off" without a clear cause.
- **Leave breathing room.** Do not fill every inch. Empty space is part of the composition, not a failure.
- **Text box padding**: text frames in python-pptx have default left/right inset of 0.1" and top/bottom inset of 0.05". When aligning lines or shapes with text edges, either set `text_frame.margin_left = 0` (etc.) or offset the shape to account for padding. Mismatched padding is the most common cause of "why does this icon sit slightly lower than the label?"

---

## 5. Motifs — pick one and commit

Every slide needs a visual element — image, chart, icon, or shape. Text-only slides are forgettable. Pick ONE of these and carry it across the whole deck.

### Layout motifs

- **Two-column** (text left, illustration right, or vice versa — but pick one direction and keep it)
- **Icon + text rows** — icon in colored circle, bold header, description below
- **2×2 or 2×3 grid** — image on one side, grid of content blocks on the other
- **Half-bleed image** — full left or right side, content overlays the other half
- **Thick single-side border** — 0.2" bar in accent color on the left edge of every content slide

### Data display motifs

- **Large stat callouts** — big numbers 60–96pt with small labels below
- **Comparison columns** — before/after, pros/cons, side-by-side options
- **Timeline / process flow** — numbered steps, arrows, connected by a thin rule

### Visual polish

- **Icons in small colored circles** next to section headers
- **Italic accent text** for key stats or taglines
- **Rounded image frames** with 0.15–0.2" corner radius

---

## 6. Common mistakes to avoid

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides.
- **Don't center body text** — left-align paragraphs and lists; center only titles.
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14–16pt body.
- **Don't default to blue** — pick colors that reflect the specific topic.
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently.
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout.
- **Don't create text-only slides** — add images, icons, charts, or visual elements.
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set margin to 0 on the text box or offset the shape to account for padding.
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background.
- **NEVER use thin horizontal accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead.

---

## 7. Databricks-delivery considerations

When the deck will be opened inside Databricks (rendered to PDF, shown in the notebook, downloaded from a Volume):

- **Fonts**: prefer web-safe fonts OR embed custom fonts in the pptx (python-pptx `core_properties` won't do this — use the XML-level approach documented in python-pptx.md).
- **File size**: if embedding many high-resolution images, the resulting pptx can exceed Volume upload limits for some workspaces. Compress images to ≤150 DPI for slide-display use.
- **Color profile**: Databricks-rendered PDFs use the cluster's default color profile (typically sRGB). Avoid any colors that rely on a specific CMYK profile for fidelity.
