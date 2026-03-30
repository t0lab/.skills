# Storytelling Framework for Databricks Dashboards

## Table of Contents

1. [Story Type Classification](#1-story-type-classification)
2. [Story → Chart Mapping](#2-story--chart-mapping)
3. [Dashboard Narrative Patterns](#3-dashboard-narrative-patterns)
4. [SQL Query Analysis → Story Detection](#4-sql-query-analysis--story-detection)
5. [Layout Composition Rules](#5-layout-composition-rules)

---

## 1. Story Type Classification

Every dashboard tells a story. Identify the story type FIRST, then choose charts.

### Primary Story Types

| Story Type | Core Question | Signal Words in User Request |
|---|---|---|
| **Magnitude** | How much? How many? | "total", "count", "KPI", "metric", "how many" |
| **Trend** | How has it changed over time? | "over time", "trend", "growth", "monthly", "yearly", "forecast" |
| **Composition** | What makes up the whole? | "breakdown", "share", "proportion", "percentage", "split" |
| **Comparison** | How does A differ from B? | "compare", "vs", "difference", "rank", "top/bottom" |
| **Correlation** | Is there a relationship? | "relationship", "correlation", "impact", "affect", "driver" |
| **Distribution** | How is data spread? | "distribution", "range", "spread", "frequency", "outlier" |
| **Geographic** | Where is it happening? | "region", "country", "location", "map", "geographic" |
| **Flow** | How do things move/convert? | "funnel", "conversion", "flow", "journey", "pipeline", "path" |
| **Cumulative Impact** | What adds up to the total? | "waterfall", "P&L", "contribute", "bridge", "buildup" |

### Compound Stories (Most Dashboards)

Real dashboards combine multiple story types. The **primary story** determines the hero chart;
**secondary stories** fill supporting positions.

```
Executive Dashboard = Magnitude (counters) + Trend (line) + Comparison (bar)
Marketing Dashboard = Flow (funnel) + Trend (line) + Geographic (map)
Financial Dashboard = Cumulative Impact (waterfall) + Trend (line) + Composition (pie)
Operations Dashboard = Distribution (histogram) + Trend (line) + Comparison (bar)
```

---

## 2. Story → Chart Mapping

### Decision Matrix

```
Story Type          → Primary Chart       → Alternative          → Supporting Charts
─────────────────────────────────────────────────────────────────────────────────────
Magnitude           → counter             → table                → sparkline in counter
Trend               → line                → area (volume feel)   → counter (current val)
Composition         → pie (≤6 cats)       → bar (stacked)        → table (detail)
Comparison          → bar                 → combo (diff scales)  → counter (delta)
Correlation         → scatter             → bubble (+3rd dim)    → heatmap (density)
Distribution        → histogram           → box (by category)    → table (stats)
Geographic          → choropleth (region) → pointMap (lat/lng)   → bar (top regions)
Flow (linear)       → funnel              → bar (horizontal)     → counter (conversion %)
Flow (multi-path)   → sankey              → (none)               → table (detail)
Cumulative Impact   → waterfall           → bar (stacked)        → counter (net total)
```

### Chart Selection Rules

1. **Counter always comes first** — Every dashboard should open with 2-4 counters showing
   the most critical KPIs. This anchors the viewer.

2. **Hero chart = primary story** — The largest chart (width=4-6) should directly answer
   the main question the dashboard exists to answer.

3. **One chart, one message** — Each chart should answer exactly one question. If you need
   to show two things, use two charts.

4. **Pie charts: max 6 slices** — More than 6 categories → use bar chart instead.
   Consider using "Other" to group small categories.

5. **Time on X-axis** — When time is involved, it ALWAYS goes on X. Never on Y.

6. **Consistent colors** — If "Product A" is blue in one chart, it must be blue everywhere.
   Use the color encoding's fieldName consistently across widgets.

7. **Detail at the bottom** — Tables go at the bottom of the dashboard. They're for
   drill-down, not for first impression.

---

## 3. Dashboard Narrative Patterns

### Pattern 1: "The Overview" (Most Common)

**Use when**: User says "give me a dashboard for X" without specific direction.

```
Row 1: Filters (date range, category selectors)
Row 2: Counter → Counter → Counter → Counter (4 KPIs across full width)
Row 3: Line chart (primary trend, full width or 4-col)
Row 4: Bar chart (comparison) | Pie chart (composition)
Row 5: Table (detail, full width)
```

**Storytelling flow**: "Here's where we stand (counters) → Here's how we got here (trend)
→ Here's what's driving it (breakdown) → Here are the details (table)"

### Pattern 2: "The Funnel Story"

**Use when**: Conversion, pipeline, user journey analysis.

```
Row 1: Counter (total input) → Counter (total output) → Counter (overall conversion %)
Row 2: Funnel chart (full width)
Row 3: Line chart (conversion trend over time) | Bar chart (conversion by segment)
Row 4: Table (stage-by-stage detail)
```

**Storytelling flow**: "Here's the big picture (counters) → Here's where we lose people (funnel)
→ Here's how it's trending (line) → Here's who converts best (bar)"

### Pattern 3: "The Comparison Story"

**Use when**: A vs B, rankings, benchmarking.

```
Row 1: Counter (A metric) → Counter (B metric) → Counter (difference/ratio)
Row 2: Combo chart (both metrics on same X-axis, dual Y)
Row 3: Bar chart (ranking) | Scatter (correlation between metrics)
Row 4: Table (full comparison detail)
```

### Pattern 4: "The Geographic Story"

**Use when**: Regional performance, location-based analysis.

```
Row 1: Counter (total) → Counter (top region) → Counter (growth leader)
Row 2: Choropleth map (full width)
Row 3: Bar chart (top N regions) | Line chart (regional trend)
Row 4: Table (all regions detail)
```

### Pattern 5: "The Financial Story"

**Use when**: P&L, revenue analysis, cost breakdown.

```
Row 1: Counter (revenue) → Counter (cost) → Counter (profit) → Counter (margin %)
Row 2: Waterfall chart (P&L bridge, full width)
Row 3: Line chart (trend) | Pie/Bar (cost breakdown)
Row 4: Table (line items)
```

### Pattern 6: "The Operational Story"

**Use when**: Performance monitoring, SLA tracking, resource utilization.

```
Row 1: Counter (current load) → Counter (avg response time) → Counter (error rate)
Row 2: Line chart (metrics over time, full width)
Row 3: Histogram (response time distribution) | Heatmap (activity by hour/day)
Row 4: Box plot (performance by category) or Table (incidents)
```

---

## 4. SQL Query Analysis → Story Detection

When the user provides SQL queries, analyze them to detect the story type automatically.

### SQL Pattern → Story Type

| SQL Pattern | Detected Story | Recommended Chart |
|---|---|---|
| `GROUP BY date_col` | Trend | line, area |
| `GROUP BY category` without date | Comparison | bar |
| `SUM/COUNT` with single row result | Magnitude | counter |
| `GROUP BY region/country/state` | Geographic | choropleth |
| Two numeric columns, no GROUP BY | Correlation | scatter |
| `GROUP BY date, GROUP BY category` | Trend + Comparison | line with color encoding |
| Subquery with stages/steps | Flow | funnel |
| `stage1, stage2, value` columns | Multi-path flow | sankey |
| Positive and negative values, sequential | Cumulative Impact | waterfall |
| Single numeric column, many rows | Distribution | histogram |
| `PERCENTILE`, `MEDIAN`, `STDDEV` | Distribution | box |
| `LAG()`, `LEAD()`, window functions | Trend + Comparison | combo (actual vs previous) |
| `PIVOT` or cross-tab | Matrix view | pivot or heatmap |
| Retention/cohort pattern | Cohort analysis | pivot with color scale |

### Column Type → Encoding Mapping

```
Column Type           → Encoding Role
──────────────────────────────────────
DATE/TIMESTAMP        → x-axis (temporal scale)
VARCHAR/STRING (low cardinality)  → color / x-axis (categorical)
VARCHAR/STRING (high cardinality) → table column / filter
INTEGER/FLOAT (measure)           → y-axis / value / size
FLOAT (ratio/percentage)          → y-axis / counter value
LATITUDE              → latitude encoding
LONGITUDE             → longitude encoding
```

### Aggregation Detection

If the SQL already contains aggregation (SUM, COUNT, AVG...), the widget transform should
typically be `None` to avoid double-aggregation. If the SQL returns raw rows, the widget
should apply the appropriate transform.

```
SQL has GROUP BY + SUM(revenue) → widget transform: None, disaggregated: false
SQL returns raw rows            → widget transform: "SUM", disaggregated: false
SQL returns per-row detail      → widget transform: None, disaggregated: true (for scatter)
```

---

## 5. Layout Composition Rules

### Grid Positioning

The dashboard grid is 6 columns wide. Heights are in grid units.

```python
# Standard widget sizes
SIZES = {
    "filter":    {"width": 2, "height": 1},
    "counter":   {"width": 1, "height": 2},  # or width=2 for wide counters
    "hero_chart": {"width": 6, "height": 6}, # full-width primary chart
    "half_chart": {"width": 3, "height": 5}, # side-by-side charts
    "third_chart": {"width": 2, "height": 5},
    "table":     {"width": 6, "height": 6},  # full-width detail table
    "map":       {"width": 6, "height": 8},  # maps need more height
}
```

### Y-Position Calculation

Widgets stack vertically. Calculate y positions by accumulating heights:

```python
y = 0
# Row 1: Filters
y_filters = 0    # height = 1
y += 1

# Row 2: Counters
y_counters = y   # height = 2
y += 2

# Row 3: Hero chart
y_hero = y       # height = 6
y += 6

# Row 4: Two side-by-side charts
y_side = y       # height = 5
y += 5

# Row 5: Table
y_table = y      # height = 6
```

### Responsive Layout Tips

- Counters should fill full width (4 counters × width=1 + 1 spacer, or 3 × width=2)
- Never put a chart in a single column (width=1) — minimum width=2 for any chart
- Tables always full width (width=6)
- Maps always full width (width=6) and extra tall (height=8)
- Side-by-side charts: left at x=0 width=3, right at x=3 width=3

### Color Palette Strategy

For consistent storytelling, assign colors by business meaning:

```
Revenue/Positive  → Green tones
Cost/Negative     → Red tones
Primary metric    → Blue (Databricks default primary)
Secondary metric  → Orange
Neutral/Total     → Gray
```

Use the color encoding's `scale` property for categorical distinctions.
For sequential data (heatmaps), use built-in color ramps like "Green Blue" or "Blue Purple".
