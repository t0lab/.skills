# serialized_dashboard Schema Reference

## Table of Contents

1. [Root Structure](#1-root-structure)
2. [Dataset](#2-dataset)
3. [Page & Layout](#3-page--layout)
4. [Widget](#4-widget)
5. [Widget Spec & Encodings](#5-widget-spec--encodings)
6. [Complete Minimal Example](#6-complete-minimal-example)

---

## 1. Root Structure

```python
{
    "pages": [Page],              # required — list of dashboard pages
    "datasets": [Dataset],        # SQL query definitions
    "uiSettings": {               # optional
        "theme": {
            "widgetHeaderAlignment": "ALIGNMENT_LEFT"  # or ALIGNMENT_CENTER
        },
        "applyModeEnabled": false  # false = filters apply immediately
    }
}
```

---

## 2. Dataset

```python
{
    "name": "a1b2c3d4",                    # required — unique hex ID
    "displayName": "Sales Data",            # required — human readable
    "queryLines": [                         # required — SQL split by lines
        "SELECT\n",
        "  product,\n",
        "  SUM(revenue) as total_revenue\n",
        "FROM catalog.schema.sales\n",
        "GROUP BY product\n"
    ],
    "parameters": [                         # optional — for :param_name in SQL
        {
            "displayName": "Start Date",
            "keyword": "start_date",        # matches :start_date in SQL
            "dataType": "DATE",             # STRING | INTEGER | FLOAT | DATE | TIMESTAMP
            "defaultSelection": {
                "values": {
                    "dataType": "DATE",
                    "values": [{"value": "2024-01-01"}]
                }
            }
        }
    ]
}
```

**Critical**: `queryLines` is a `list[str]`, NOT a single string. Each line ends with `\n`.

---

## 3. Page & Layout

### Page

```python
{
    "name": "b1c2d3e4",                    # required — unique hex ID
    "displayName": "Overview",              # required — tab name in UI
    "pageType": "PAGE_TYPE_CANVAS",         # required — always this value
    "layout": [LayoutItem]                  # required — list of positioned widgets
}
```

### Layout Item

```python
{
    "widget": Widget,
    "position": {
        "x": 0,        # 0–5 (6-column grid)
        "y": 0,        # 0+ (grows downward)
        "width": 3,    # 1–6
        "height": 4    # minimum 1
    }
}
```

### Grid Rules

- Grid is **6 columns** wide
- X ranges from 0 to 5
- x + width must be ≤ 6
- Y grows downward infinitely (0 = top)
- Widgets at same Y level appear side-by-side
- No overlapping allowed

---

## 4. Widget

### Chart Widget

```python
{
    "name": "c1d2e3f4",                    # required — unique hex ID
    "queries": [
        {
            "name": "main_query",
            "query": {
                "datasetName": "a1b2c3d4",  # must match Dataset.name
                "fields": [
                    {
                        "name": "product",
                        "expression": "`product`"
                    },
                    {
                        "name": "total_revenue",
                        "expression": "`total_revenue`"
                    }
                ],
                "disaggregated": false       # true = raw data, false = allow aggregate
            }
        }
    ],
    "spec": WidgetSpec                       # chart configuration
}
```

### Text Widget

```python
{
    "name": "d1e2f3a4",
    "textbox_spec": "## Dashboard Title\n\nMarkdown content here."
}
```

When `textbox_spec` is present, the widget is a text/markdown box. No `spec` or `queries` needed.

### Field Expression Syntax

```python
# Simple column reference
{"name": "col_name", "expression": "`col_name`"}

# Aggregation
{"name": "total", "expression": "SUM(`revenue`)"}

# Date truncation
{"name": "month", "expression": "DATE_TRUNC(\"MONTH\", `order_date`)"}

# Count with condition
{"name": "active", "expression": "COUNT_IF(`status` = 'active')"}
```

Note: Backquotes for column names, escaped double quotes for string literals inside expressions.

---

## 5. Widget Spec & Encodings

### WidgetSpec

```python
{
    "version": 3,                            # 2 or 3
    "widgetType": "bar",                     # see chart_type_mapping.md
    "encodings": Encodings,                  # chart-specific encodings
    "frame": {                               # optional — title/description
        "showTitle": true,
        "title": "Revenue by Product",
        "showDescription": false,
        "description": ""
    },
    "mark": {                                # optional — bar/area layout
        "layout": "group"                    # "group" | "stack" | "layered"
    }
}
```

### Axis Encoding (x / y)

```python
# Single field mode
{
    "fieldName": "column_name",
    "displayName": "Display Label",          # optional
    "scale": {
        "type": "quantitative",              # "quantitative" | "categorical" | "temporal"
        "sort": {
            "by": "y-reversed",              # sort by another encoding
            "order": "descending"
        },
        "fn": {"type": "symlog"}             # optional: "log" | "symlog" | "sqrt"
    },
    "transform": "SUM",                      # optional: SUM | AVG | COUNT | COUNT_DISTINCT | MIN | MAX | MEDIAN
    "format": {                              # optional: number formatting
        "type": "number-plain",              # "number-plain" | "number-percent" | "number-currency"
        "abbreviation": "compact"            # "compact" | "none"
    }
}

# Multi-field mode (e.g., combo chart y-axis)
{
    "fields": [
        {"fieldName": "metric_a", "displayName": "Revenue"},
        {"fieldName": "metric_b", "displayName": "Margin"}
    ],
    "scale": {"type": "quantitative"}
}
```

### Color Encoding

```python
{
    "fieldName": "category_col",
    "displayName": "Category",
    "scale": {"type": "categorical"},
    "legend": {"position": "top"}            # "top" | "bottom" | "left" | "right"
}
```

### Other Encodings

```python
# Label (data labels on bar/line/area)
"label": {"show": true}

# Value (counter)
"value": {"fieldName": "metric", "transform": "SUM"}

# Comparison (counter — shows delta)
"comparison": {"fieldName": "date_col"}

# Sparkline (counter — mini trend line)
"sparkline": {"fieldName": "date_col"}

# Angle (pie chart — the value)
"angle": {"fieldName": "amount", "transform": "SUM"}

# Size (scatter → bubble, line → thickness, pointMap → marker size)
"size": {"fieldName": "metric_col"}

# Geo (choropleth)
"geo": {"fieldName": "region_col", "level": "country"}

# Latitude / Longitude (pointMap)
"latitude": {"fieldName": "lat"}
"longitude": {"fieldName": "lng"}

# Facet (split chart into small multiples)
"facet": {"fieldName": "category_col"}

# Tooltip
"tooltip": [{"fieldName": "extra_info"}]

# Filter fields
"fields": [{"fieldName": "col", "displayName": "Label", "queryName": "main_query"}]

# Table columns
"columns": [{"fieldName": "col", "displayName": "Label", "type": "string", "order": 0}]

# Pivot
"rows": [{"fieldName": "row_dim"}]
"values": [{"fieldName": "measure", "transform": "SUM"}]
```

---

## 6. Complete Minimal Example

A dashboard with 1 counter + 1 bar chart + 1 table:

```json
{
  "datasets": [
    {
      "name": "ds001",
      "displayName": "Product Sales",
      "queryLines": [
        "SELECT\n",
        "  product_name,\n",
        "  SUM(revenue) as total_revenue,\n",
        "  COUNT(*) as order_count\n",
        "FROM catalog.schema.orders\n",
        "GROUP BY product_name\n",
        "ORDER BY total_revenue DESC\n"
      ]
    }
  ],
  "pages": [
    {
      "name": "pg001",
      "displayName": "Sales Overview",
      "pageType": "PAGE_TYPE_CANVAS",
      "layout": [
        {
          "widget": {
            "name": "w001",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "datasetName": "ds001",
                  "fields": [
                    {"name": "total_revenue", "expression": "`total_revenue`"}
                  ],
                  "disaggregated": false
                }
              }
            ],
            "spec": {
              "version": 2,
              "widgetType": "counter",
              "encodings": {
                "value": {"fieldName": "total_revenue", "transform": "SUM"}
              },
              "frame": {"showTitle": true, "title": "Total Revenue"}
            }
          },
          "position": {"x": 0, "y": 0, "width": 2, "height": 2}
        },
        {
          "widget": {
            "name": "w002",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "datasetName": "ds001",
                  "fields": [
                    {"name": "product_name", "expression": "`product_name`"},
                    {"name": "total_revenue", "expression": "`total_revenue`"}
                  ],
                  "disaggregated": false
                }
              }
            ],
            "spec": {
              "version": 3,
              "widgetType": "bar",
              "encodings": {
                "x": {"fieldName": "product_name", "scale": {"type": "categorical"}},
                "y": {"fieldName": "total_revenue", "scale": {"type": "quantitative"}, "transform": "SUM"},
                "label": {"show": true}
              },
              "frame": {"showTitle": true, "title": "Revenue by Product"}
            }
          },
          "position": {"x": 0, "y": 2, "width": 6, "height": 5}
        },
        {
          "widget": {
            "name": "w003",
            "queries": [
              {
                "name": "main_query",
                "query": {
                  "datasetName": "ds001",
                  "fields": [
                    {"name": "product_name", "expression": "`product_name`"},
                    {"name": "total_revenue", "expression": "`total_revenue`"},
                    {"name": "order_count", "expression": "`order_count`"}
                  ],
                  "disaggregated": true
                }
              }
            ],
            "spec": {
              "version": 2,
              "widgetType": "table",
              "encodings": {
                "columns": [
                  {"fieldName": "product_name", "displayName": "Product", "type": "string", "order": 0},
                  {"fieldName": "total_revenue", "displayName": "Revenue", "type": "number", "order": 1},
                  {"fieldName": "order_count", "displayName": "Orders", "type": "number", "order": 2}
                ]
              },
              "frame": {"showTitle": true, "title": "Product Details"}
            }
          },
          "position": {"x": 0, "y": 7, "width": 6, "height": 5}
        }
      ]
    }
  ]
}
```
