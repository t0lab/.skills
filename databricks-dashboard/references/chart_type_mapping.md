# Chart Type Mapping — Databricks serialized_dashboard

## Table of Contents

1. [Complete widgetType List](#1-complete-widgettype-list)
2. [Encodings Cheatsheet](#2-encodings-cheatsheet)
3. [Chart Configuration Details](#3-chart-configuration-details)
4. [Virtual Types (No Separate widgetType)](#4-virtual-types)

---

## 1. Complete widgetType List

### Version 3 — Chart Widgets

| UI Name | `widgetType` | Primary Encodings | Notes |
|---|---|---|---|
| Bar | `"bar"` | x, y, color, label, facet | mark.layout: group/stack/layered |
| Line | `"line"` | x, y, color, size, label, facet | size = line thickness |
| Area | `"area"` | x, y, color, label, facet | mark.layout: stack/layered |
| Scatter | `"scatter"` | x, y, color, size, facet | +size → Bubble chart |
| Pie | `"pie"` | angle, color | angle = value, color = category |
| Combo | `"combo"` | x, y, color, facet | Bar+Line, supports dual-axis |
| Heatmap | `"heatmap"` | x, y, color | color = cell value. Max 64K rows |
| Histogram | `"histogram"` | x | Y auto-computed (frequency). Bins configurable |
| Box | `"box"` | x, y | X = category (optional), Y = numeric |
| Funnel | `"funnel"` | x, y, color | X = step, Y = value. Max 64K rows |
| Sankey | `"sankey"` | color | NO widget aggregation. SQL must pre-aggregate |
| Waterfall | `"waterfall"` | x, y | X = category/time, Y = +/- values |
| Choropleth | `"choropleth"` | geo, color | geo.level: country/state/county |
| Point Map | `"pointMap"` | latitude, longitude, color, size | Needs lat/lng in dataset |

### Version 2 — Counter/Table/Filter Widgets

| UI Name | `widgetType` | Primary Encodings | Notes |
|---|---|---|---|
| Counter | `"counter"` | value, comparison, sparkline | Single KPI display |
| Table | `"table"` | columns | Sortable, conditional formatting |
| Pivot | `"pivot"` | rows, columns, values | Cross-tab. +color scale = Cohort |
| Filter Multi | `"filter-multi-select"` | fields | Multiple selection dropdown |
| Filter Single | `"filter-single-select"` | fields | Single selection dropdown |
| Filter Date Range | `"filter-date-range-picker"` | fields | Date range selector |
| Filter Date | `"filter-date-picker"` | fields | Single date selector |

---

## 2. Encodings Cheatsheet

```
┌─────────────────────┬────┬────┬───────┬───────┬──────┬───────┬──────┬───────┬────────┬─────────┬──────────┐
│ widgetType          │ x  │ y  │ color │ angle │ size │ facet │ geo  │ value │ fields │ columns │ rows+val │
├─────────────────────┼────┼────┼───────┼───────┼──────┼───────┼──────┼───────┼────────┼─────────┼──────────┤
│ bar           (v3)  │ ✅ │ ✅ │ ✅    │       │      │ ✅    │      │       │        │         │          │
│ line          (v3)  │ ✅ │ ✅ │ ✅    │       │ ✅¹  │ ✅    │      │       │        │         │          │
│ area          (v3)  │ ✅ │ ✅ │ ✅    │       │      │ ✅    │      │       │        │         │          │
│ scatter       (v3)  │ ✅ │ ✅ │ ✅    │       │ ✅²  │ ✅    │      │       │        │         │          │
│ pie           (v3)  │    │    │ ✅    │ ✅    │      │       │      │       │        │         │          │
│ combo         (v3)  │ ✅ │ ✅ │ ✅    │       │      │ ✅    │      │       │        │         │          │
│ heatmap       (v3)  │ ✅ │ ✅ │ ✅³   │       │      │       │      │       │        │         │          │
│ histogram     (v3)  │ ✅ │    │       │       │      │       │      │       │        │         │          │
│ box           (v3)  │ ✅ │ ✅ │       │       │      │       │      │       │        │         │          │
│ funnel        (v3)  │ ✅ │ ✅ │ ✅    │       │      │       │      │       │        │         │          │
│ sankey        (v3)  │    │    │ ✅    │       │      │       │      │       │        │         │          │
│ waterfall     (v3)  │ ✅ │ ✅ │       │       │      │       │      │       │        │         │          │
│ choropleth    (v3)  │    │    │ ✅    │       │      │       │ ✅   │       │        │         │          │
│ pointMap      (v3)  │    │    │ ✅    │       │ ✅   │       │      │       │        │         │          │
│ counter       (v2)  │    │    │       │       │      │       │      │ ✅    │        │         │          │
│ table         (v2)  │    │    │       │       │      │       │      │       │        │ ✅      │          │
│ pivot         (v2)  │    │    │       │       │      │       │      │       │        │ ✅      │ ✅       │
│ filter-*      (v2)  │    │    │       │       │      │       │      │       │ ✅     │         │          │
└─────────────────────┴────┴────┴───────┴───────┴──────┴───────┴──────┴───────┴────────┴─────────┴──────────┘

¹ size = line thickness    ² size = bubble radius    ³ color = cell fill value
```

---

## 3. Chart Configuration Details

### Bar Chart

```json
{
  "version": 3,
  "widgetType": "bar",
  "encodings": {
    "x": {"fieldName": "category_col", "scale": {"type": "categorical"}},
    "y": {"fieldName": "value_col", "scale": {"type": "quantitative"}, "transform": "SUM"},
    "color": {"fieldName": "group_col"},
    "label": {"show": true}
  },
  "mark": {"layout": "group"}
}
```

**mark.layout options**: `"group"` (side-by-side), `"stack"` (stacked), `"layered"` (100% stack)

### Line Chart

```json
{
  "version": 3,
  "widgetType": "line",
  "encodings": {
    "x": {"fieldName": "date_col", "scale": {"type": "temporal"}, "transform": "MONTHLY"},
    "y": {"fieldName": "metric_col", "scale": {"type": "quantitative"}, "transform": "SUM"},
    "color": {"fieldName": "series_col"}
  }
}
```

**X-axis temporal transforms**: `"DAILY"`, `"WEEKLY"`, `"MONTHLY"`, `"QUARTERLY"`, `"YEARLY"`

### Counter

```json
{
  "version": 2,
  "widgetType": "counter",
  "encodings": {
    "value": {"fieldName": "metric_col", "transform": "SUM"},
    "comparison": {"fieldName": "date_col"},
    "sparkline": {"fieldName": "date_col"}
  }
}
```

### Pie Chart

```json
{
  "version": 3,
  "widgetType": "pie",
  "encodings": {
    "angle": {"fieldName": "value_col", "transform": "SUM"},
    "color": {"fieldName": "category_col"}
  }
}
```

### Scatter / Bubble

```json
{
  "version": 3,
  "widgetType": "scatter",
  "encodings": {
    "x": {"fieldName": "metric_a", "scale": {"type": "quantitative"}},
    "y": {"fieldName": "metric_b", "scale": {"type": "quantitative"}},
    "color": {"fieldName": "category_col"},
    "size": {"fieldName": "metric_c"}
  }
}
```

Adding `size` encoding automatically creates a bubble chart.

### Funnel

```json
{
  "version": 3,
  "widgetType": "funnel",
  "encodings": {
    "x": {"fieldName": "stage_col", "scale": {"type": "categorical"}},
    "y": {"fieldName": "count_col", "scale": {"type": "quantitative"}, "transform": "SUM"}
  }
}
```

### Sankey

```json
{
  "version": 3,
  "widgetType": "sankey",
  "encodings": {
    "color": {}
  }
}
```

**Critical**: Sankey requires SQL query with columns named `stage1`, `stage2`, `value`.
All aggregation MUST be in the SQL query. No widget-level transforms.

### Waterfall

```json
{
  "version": 3,
  "widgetType": "waterfall",
  "encodings": {
    "x": {"fieldName": "category_col", "scale": {"type": "categorical"}},
    "y": {"fieldName": "amount_col", "scale": {"type": "quantitative"}, "transform": "SUM"}
  }
}
```

### Histogram

```json
{
  "version": 3,
  "widgetType": "histogram",
  "encodings": {
    "x": {"fieldName": "numeric_col"}
  }
}
```

Bins configuration may be at spec level (e.g., `numberOfBins: 20`).

### Box Chart

```json
{
  "version": 3,
  "widgetType": "box",
  "encodings": {
    "x": {"fieldName": "category_col", "scale": {"type": "categorical"}},
    "y": {"fieldName": "numeric_col", "scale": {"type": "quantitative"}}
  }
}
```

### Choropleth Map

```json
{
  "version": 3,
  "widgetType": "choropleth",
  "encodings": {
    "geo": {"fieldName": "region_col", "level": "country"},
    "color": {"fieldName": "metric_col", "scale": {"type": "quantitative"}}
  }
}
```

**geo.level**: `"country"`, `"state"`, `"county"`

### Point Map

```json
{
  "version": 3,
  "widgetType": "pointMap",
  "encodings": {
    "latitude": {"fieldName": "lat_col"},
    "longitude": {"fieldName": "lng_col"},
    "color": {"fieldName": "category_col"},
    "size": {"fieldName": "metric_col"}
  }
}
```

### Combo (Dual-Axis)

```json
{
  "version": 3,
  "widgetType": "combo",
  "encodings": {
    "x": {"fieldName": "date_col", "scale": {"type": "temporal"}},
    "y": {
      "fields": [
        {"fieldName": "bar_metric", "displayName": "Revenue"},
        {"fieldName": "line_metric", "displayName": "Margin %"}
      ]
    },
    "color": {}
  }
}
```

### Table

```json
{
  "version": 2,
  "widgetType": "table",
  "encodings": {
    "columns": [
      {"fieldName": "col1", "displayName": "Column 1", "type": "string", "order": 0},
      {"fieldName": "col2", "displayName": "Column 2", "type": "number", "order": 1}
    ]
  }
}
```

### Pivot

```json
{
  "version": 2,
  "widgetType": "pivot",
  "encodings": {
    "rows": [{"fieldName": "row_dimension"}],
    "columns": [{"fieldName": "col_dimension"}],
    "values": [{"fieldName": "measure_col", "transform": "SUM"}]
  }
}
```

### Filters

```json
{
  "version": 2,
  "widgetType": "filter-multi-select",
  "encodings": {
    "fields": [
      {"fieldName": "filter_col", "displayName": "Select Category", "queryName": "main_query"}
    ]
  }
}
```

---

## 4. Virtual Types

These chart types appear in the Databricks UI but do NOT have their own `widgetType`:

| UI Name | Actual widgetType | How to achieve |
|---|---|---|
| Bubble Chart | `"scatter"` | Add `size` encoding with a metric field |
| Cohort Chart | `"pivot"` | Use retention SQL + set cell style to "Color Scale" |
| Dual-axis Chart | `"combo"` | Enable dual axis in y encoding settings |
| Line Forecast | `"line"` | Enable forecast config in widget spec |
