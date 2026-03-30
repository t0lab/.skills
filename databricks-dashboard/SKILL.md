---
name: databricks-dashboard
description: >
  Create, design, and publish Databricks AI/BI dashboards programmatically using the Lakeview API
  and WorkspaceClient (databricks-sdk). This skill handles the FULL pipeline: analyzing user intent
  and SQL queries → storytelling strategy (which charts tell the best story) → generating
  serialized_dashboard JSON → creating and publishing via API.

  USE THIS SKILL whenever the user mentions: Databricks dashboard, lakeview dashboard, AI/BI dashboard,
  lvdash.json, serialized_dashboard, dashboard creation, dashboard storytelling, data visualization
  on Databricks, or wants to turn SQL queries into visual dashboards. Also trigger when the user has
  SQL queries and wants to understand what story the data tells, or needs help choosing chart types
  for their Databricks dashboard.
---

# Databricks Dashboard Skill

## Overview

This skill creates Databricks AI/BI (Lakeview) dashboards programmatically. It follows a
**storytelling-first** approach:

1. **Understand the story** — What question does the data answer? What insight should jump out?
2. **Design the layout** — Which charts, in what order, to guide the viewer through the narrative
3. **Generate the JSON** — Build valid `serialized_dashboard` spec
4. **Deploy** — Create + publish via WorkspaceClient

## Workflow

### Step 1: Analyze Intent & Data

When the user provides SQL queries or a text description, determine:

- **Audience**: Who will view this dashboard? (executives → counters + high-level; analysts → detailed)
- **Story type**: What narrative pattern fits? (see Storytelling Framework below)
- **Data shape**: What columns/metrics are available from the SQL queries?

Read `references/storytelling_framework.md` for the complete storytelling decision tree.

### Step 2: Design Dashboard (Story → Charts)

Map the story to concrete chart selections using this priority:

```
User Query / Description
    ↓
Identify Story Type (from storytelling_framework.md)
    ↓
Select Chart Types (from references/chart_type_mapping.md)
    ↓
Determine Layout (grid positions, grouping, flow)
    ↓
Generate serialized_dashboard JSON
```

Read `references/chart_type_mapping.md` for the complete widgetType reference including
encodings, version numbers, and encoding cheatsheet.

### Step 3: Build serialized_dashboard JSON

Read `references/schema_reference.md` for the complete TypedDict schema of the
serialized_dashboard JSON structure. Key rules:

- Dataset queries use `queryLines` (list[str]), NOT `query` (str)
- Each query line ends with `\n`
- Grid is 6 columns wide, Y grows downward infinitely
- Widget names and page names are hex IDs (e.g., "a1b2c3d4")
- version 2 = counter, table, pivot, filter-*
- version 3 = all other chart types

### Step 4: Create & Publish

Use the scripts to deploy:

```python
# Step 1: Create draft dashboard
python scripts/create_dashboard.py \
    --name "My Dashboard" \
    --warehouse-id "abc123" \
    --json-path ./dashboard.json

# Step 2: Publish
python scripts/publish_dashboard.py \
    --dashboard-id "<id-from-step-1>" \
    --warehouse-id "abc123"
```

Or use directly in code — see `scripts/create_dashboard.py` and `scripts/publish_dashboard.py`
for the WorkspaceClient integration.

## Storytelling Framework (Quick Reference)

The full framework is in `references/storytelling_framework.md`. Here's the decision tree:

```
What is the user trying to communicate?
│
├─ "How much / How many?" (magnitude)
│   → Counter (KPI) + supporting Bar or Line
│
├─ "How has it changed?" (trend over time)
│   → Line / Area chart as hero, Counters for current values
│
├─ "What's the breakdown?" (composition)
│   → Pie (≤6 categories) or Stacked Bar (>6 or over time)
│
├─ "How does A compare to B?" (comparison)
│   → Bar (categorical) or Combo (different scales)
│
├─ "Is there a relationship?" (correlation)
│   → Scatter / Bubble
│
├─ "Where?" (geographic)
│   → Choropleth (regions) or Point Map (lat/lng)
│
├─ "What's the distribution?" (spread)
│   → Histogram or Box plot
│
├─ "How do users/items flow?" (flow/conversion)
│   → Funnel (linear stages) or Sankey (multi-path)
│
├─ "What contributes to the total?" (cumulative impact)
│   → Waterfall
│
└─ "Show me everything" (overview dashboard)
    → Counter row (top KPIs) → Line/Area (trend) → Bar (breakdown)
    → Table (detail) at bottom
```

## Layout Best Practices

### Grid System
- 6 columns wide
- Counters: width=1 or 2, height=2 (top row)
- Charts: width=3, height=4-6 (middle)
- Tables: width=6, height=4-8 (bottom, full width)
- Filters: width=2, height=1 (top, before charts)

### Dashboard Flow (top → bottom)
```
┌──────────────────────────────────────────────┐
│  [Filter 1]  [Filter 2]  [Filter 3]         │  y=0, h=1
├──────────────────────────────────────────────┤
│  [Counter]  [Counter]  [Counter]  [Counter]  │  y=1, h=2
├──────────────────────────────────────────────┤
│  [Hero Chart — Line/Area trend]              │  y=3, h=6
├──────────────────────────────────────────────┤
│  [Bar Chart]          │  [Pie Chart]         │  y=9, h=5
├──────────────────────────────────────────────┤
│  [Detail Table — full width]                 │  y=14, h=6
└──────────────────────────────────────────────┘
```

### Naming Conventions
- Page names: 8-char hex (`"a1b2c3d4"`)
- Widget names: 8-char hex, unique per dashboard
- Dataset names: 8-char hex
- Display names: human-readable, descriptive

## Important Constraints

1. **Sankey**: No widget-level aggregation — all aggregation must be in SQL
2. **Histogram**: Only needs x encoding — y is auto-computed (frequency)
3. **Bubble**: Not a separate widgetType — use `"scatter"` + size encoding
4. **Cohort**: Not a separate widgetType — use `"pivot"` + retention SQL + color scale
5. **Forecast**: Not a separate widgetType — use `"line"` + forecast config
6. **Heatmap**: Max 64K rows or 10MB
7. **Funnel**: Max 64K rows for aggregation

## Error Handling

Common issues and fixes:
- `INVALID_PARAMETER_VALUE` → Check queryLines format (must be list[str] ending with \n)
- Widget not rendering → Verify widgetType string matches exactly (case-sensitive, camelCase)
- Empty chart → Check that dataset name in widget query matches dataset definition
- Filter not working → Ensure filter widget's queryName matches the target widget query name

## File Reference

| File | Purpose | When to read |
|------|---------|-------------|
| `references/storytelling_framework.md` | Story type → chart selection logic | When analyzing user intent |
| `references/chart_type_mapping.md` | Complete widgetType + encodings reference | When building widget spec |
| `references/schema_reference.md` | Full serialized_dashboard TypedDict schema | When generating JSON |
| `scripts/create_dashboard.py` | WorkspaceClient create dashboard | When deploying |
| `scripts/publish_dashboard.py` | WorkspaceClient publish dashboard | When deploying |
| `scripts/build_dashboard_json.py` | Helper to assemble serialized_dashboard | When generating JSON |
| `examples/sales_dashboard.json` | Complete example dashboard JSON | For reference |
