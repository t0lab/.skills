"""
build_dashboard_json.py — Build serialized_dashboard JSON from high-level config.

This module provides builder helpers that simplify constructing the nested
serialized_dashboard structure. It is used by the agent to translate a
storytelling plan into a valid .lvdash.json payload.

Usage:
    from build_dashboard_json import DashboardBuilder

    db = DashboardBuilder("Sales Overview")
    ds = db.add_dataset("Sales Data", [
        "SELECT product, SUM(revenue) as rev\\n",
        "FROM catalog.schema.sales\\n",
        "GROUP BY product\\n",
    ])
    pg = db.add_page("Overview")

    pg.add_counter(ds, "rev", title="Total Revenue", position=(0, 0, 2, 2))
    pg.add_bar(ds, x="product", y="rev", title="Revenue by Product", position=(0, 2, 6, 5))
    pg.add_table(ds, columns=["product", "rev"], title="Details", position=(0, 7, 6, 5))

    json_str = db.to_json()
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional


def _hex_id() -> str:
    """Generate an 8-char hex ID for names."""
    return uuid.uuid4().hex[:8]


class PageBuilder:
    """Builder for a single dashboard page."""

    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name
        self.layout: list[dict] = []

    def _make_widget(
        self,
        dataset_name: str,
        fields: list[dict],
        spec: dict,
        position: tuple[int, int, int, int],
        disaggregated: bool = False,
    ) -> dict:
        x, y, w, h = position
        return {
            "widget": {
                "name": _hex_id(),
                "queries": [
                    {
                        "name": "main_query",
                        "query": {
                            "datasetName": dataset_name,
                            "fields": fields,
                            "disaggregated": disaggregated,
                        },
                    }
                ],
                "spec": spec,
            },
            "position": {"x": x, "y": y, "width": w, "height": h},
        }

    @staticmethod
    def _field(name: str, expression: Optional[str] = None) -> dict:
        return {"name": name, "expression": expression or f"`{name}`"}

    # ─── Chart builders ────────────────────────────────────────────

    def add_counter(
        self,
        dataset_name: str,
        value_field: str,
        *,
        title: str = "",
        transform: str = "SUM",
        comparison_field: Optional[str] = None,
        position: tuple[int, int, int, int] = (0, 0, 2, 2),
    ):
        fields = [self._field(value_field)]
        encodings: dict[str, Any] = {
            "value": {"fieldName": value_field, "transform": transform}
        }
        if comparison_field:
            fields.append(self._field(comparison_field))
            encodings["comparison"] = {"fieldName": comparison_field}

        spec = {
            "version": 2,
            "widgetType": "counter",
            "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_bar(
        self,
        dataset_name: str,
        *,
        x: str,
        y: str,
        title: str = "",
        color: Optional[str] = None,
        transform: str = "SUM",
        layout: str = "group",
        position: tuple[int, int, int, int] = (0, 0, 6, 5),
    ):
        fields = [self._field(x), self._field(y)]
        encodings: dict[str, Any] = {
            "x": {"fieldName": x, "scale": {"type": "categorical"}},
            "y": {"fieldName": y, "scale": {"type": "quantitative"}, "transform": transform},
            "label": {"show": True},
        }
        if color:
            fields.append(self._field(color))
            encodings["color"] = {"fieldName": color}

        spec = {
            "version": 3,
            "widgetType": "bar",
            "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
            "mark": {"layout": layout},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_line(
        self,
        dataset_name: str,
        *,
        x: str,
        y: str,
        title: str = "",
        color: Optional[str] = None,
        x_temporal_transform: Optional[str] = None,
        y_transform: str = "SUM",
        position: tuple[int, int, int, int] = (0, 0, 6, 5),
    ):
        fields = [self._field(x), self._field(y)]
        x_enc: dict[str, Any] = {"fieldName": x, "scale": {"type": "temporal"}}
        if x_temporal_transform:
            x_enc["transform"] = x_temporal_transform

        encodings: dict[str, Any] = {
            "x": x_enc,
            "y": {"fieldName": y, "scale": {"type": "quantitative"}, "transform": y_transform},
        }
        if color:
            fields.append(self._field(color))
            encodings["color"] = {"fieldName": color}

        spec = {
            "version": 3,
            "widgetType": "line",
            "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_area(self, dataset_name: str, *, x: str, y: str, title: str = "",
                 color: Optional[str] = None, y_transform: str = "SUM",
                 layout: str = "stack",
                 position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y)]
        encodings: dict[str, Any] = {
            "x": {"fieldName": x, "scale": {"type": "temporal"}},
            "y": {"fieldName": y, "scale": {"type": "quantitative"}, "transform": y_transform},
        }
        if color:
            fields.append(self._field(color))
            encodings["color"] = {"fieldName": color}
        spec = {
            "version": 3, "widgetType": "area", "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
            "mark": {"layout": layout},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_pie(self, dataset_name: str, *, angle: str, color: str, title: str = "",
                transform: str = "SUM",
                position: tuple[int, int, int, int] = (0, 0, 3, 5)):
        fields = [self._field(angle), self._field(color)]
        spec = {
            "version": 3, "widgetType": "pie",
            "encodings": {
                "angle": {"fieldName": angle, "transform": transform},
                "color": {"fieldName": color},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_scatter(self, dataset_name: str, *, x: str, y: str, title: str = "",
                    color: Optional[str] = None, size: Optional[str] = None,
                    position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y)]
        encodings: dict[str, Any] = {
            "x": {"fieldName": x, "scale": {"type": "quantitative"}},
            "y": {"fieldName": y, "scale": {"type": "quantitative"}},
        }
        if color:
            fields.append(self._field(color))
            encodings["color"] = {"fieldName": color}
        if size:
            fields.append(self._field(size))
            encodings["size"] = {"fieldName": size}
        spec = {
            "version": 3, "widgetType": "scatter", "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_combo(self, dataset_name: str, *, x: str, y_fields: list[dict], title: str = "",
                  position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x)] + [self._field(f["fieldName"]) for f in y_fields]
        spec = {
            "version": 3, "widgetType": "combo",
            "encodings": {
                "x": {"fieldName": x, "scale": {"type": "temporal"}},
                "y": {"fields": y_fields},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_funnel(self, dataset_name: str, *, x: str, y: str, title: str = "",
                   y_transform: str = "SUM",
                   position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y)]
        spec = {
            "version": 3, "widgetType": "funnel",
            "encodings": {
                "x": {"fieldName": x, "scale": {"type": "categorical"}},
                "y": {"fieldName": y, "scale": {"type": "quantitative"}, "transform": y_transform},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_sankey(self, dataset_name: str, *, title: str = "",
                   position: tuple[int, int, int, int] = (0, 0, 6, 6)):
        spec = {
            "version": 3, "widgetType": "sankey",
            "encodings": {},
            "frame": {"showTitle": bool(title), "title": title},
        }
        # Sankey uses all columns from the query directly
        self.layout.append(self._make_widget(dataset_name, [], spec, position))

    def add_waterfall(self, dataset_name: str, *, x: str, y: str, title: str = "",
                      y_transform: str = "SUM",
                      position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y)]
        spec = {
            "version": 3, "widgetType": "waterfall",
            "encodings": {
                "x": {"fieldName": x, "scale": {"type": "categorical"}},
                "y": {"fieldName": y, "scale": {"type": "quantitative"}, "transform": y_transform},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_histogram(self, dataset_name: str, *, x: str, title: str = "",
                      position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x)]
        spec = {
            "version": 3, "widgetType": "histogram",
            "encodings": {"x": {"fieldName": x}},
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_box(self, dataset_name: str, *, x: str, y: str, title: str = "",
                position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y)]
        spec = {
            "version": 3, "widgetType": "box",
            "encodings": {
                "x": {"fieldName": x, "scale": {"type": "categorical"}},
                "y": {"fieldName": y, "scale": {"type": "quantitative"}},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_heatmap(self, dataset_name: str, *, x: str, y: str, color: str, title: str = "",
                    color_transform: str = "SUM",
                    position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(x), self._field(y), self._field(color)]
        spec = {
            "version": 3, "widgetType": "heatmap",
            "encodings": {
                "x": {"fieldName": x, "scale": {"type": "categorical"}},
                "y": {"fieldName": y, "scale": {"type": "categorical"}},
                "color": {"fieldName": color, "scale": {"type": "quantitative"}, "transform": color_transform},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_choropleth(self, dataset_name: str, *, geo: str, color: str, title: str = "",
                       geo_level: str = "country", color_transform: str = "SUM",
                       position: tuple[int, int, int, int] = (0, 0, 6, 8)):
        fields = [self._field(geo), self._field(color)]
        spec = {
            "version": 3, "widgetType": "choropleth",
            "encodings": {
                "geo": {"fieldName": geo, "level": geo_level},
                "color": {"fieldName": color, "scale": {"type": "quantitative"}, "transform": color_transform},
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_point_map(self, dataset_name: str, *, lat: str, lng: str, title: str = "",
                      color: Optional[str] = None, size: Optional[str] = None,
                      position: tuple[int, int, int, int] = (0, 0, 6, 8)):
        fields = [self._field(lat), self._field(lng)]
        encodings: dict[str, Any] = {
            "latitude": {"fieldName": lat},
            "longitude": {"fieldName": lng},
        }
        if color:
            fields.append(self._field(color))
            encodings["color"] = {"fieldName": color}
        if size:
            fields.append(self._field(size))
            encodings["size"] = {"fieldName": size}
        spec = {
            "version": 3, "widgetType": "pointMap", "encodings": encodings,
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_table(
        self,
        dataset_name: str,
        columns: list[str | dict],
        *,
        title: str = "",
        position: tuple[int, int, int, int] = (0, 0, 6, 5),
    ):
        col_specs = []
        fields = []
        for i, col in enumerate(columns):
            if isinstance(col, str):
                col_specs.append({"fieldName": col, "displayName": col, "type": "string", "order": i})
                fields.append(self._field(col))
            else:
                col_specs.append({**col, "order": col.get("order", i)})
                fields.append(self._field(col["fieldName"]))

        spec = {
            "version": 2,
            "widgetType": "table",
            "encodings": {"columns": col_specs},
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(
            self._make_widget(dataset_name, fields, spec, position, disaggregated=True)
        )

    def add_pivot(self, dataset_name: str, *, rows: list[str], columns: list[str],
                  values: list[dict], title: str = "",
                  position: tuple[int, int, int, int] = (0, 0, 6, 5)):
        fields = [self._field(r) for r in rows] + [self._field(c) for c in columns]
        fields += [self._field(v["fieldName"]) for v in values]
        spec = {
            "version": 2, "widgetType": "pivot",
            "encodings": {
                "rows": [{"fieldName": r} for r in rows],
                "columns": [{"fieldName": c} for c in columns],
                "values": values,
            },
            "frame": {"showTitle": bool(title), "title": title},
        }
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_filter(self, dataset_name: str, *, field: str, display_name: str = "",
                   filter_type: str = "filter-multi-select",
                   position: tuple[int, int, int, int] = (0, 0, 2, 1)):
        spec = {
            "version": 2,
            "widgetType": filter_type,
            "encodings": {
                "fields": [
                    {"fieldName": field, "displayName": display_name or field, "queryName": "main_query"}
                ]
            },
        }
        fields = [self._field(field)]
        self.layout.append(self._make_widget(dataset_name, fields, spec, position))

    def add_text(self, markdown: str, *, position: tuple[int, int, int, int] = (0, 0, 6, 2)):
        self.layout.append({
            "widget": {"name": _hex_id(), "textbox_spec": markdown},
            "position": {"x": position[0], "y": position[1], "width": position[2], "height": position[3]},
        })

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "pageType": "PAGE_TYPE_CANVAS",
            "layout": self.layout,
        }


class DashboardBuilder:
    """Top-level builder for serialized_dashboard."""

    def __init__(self, title: str = "Dashboard"):
        self.title = title
        self.datasets: list[dict] = []
        self.pages: list[PageBuilder] = []

    def add_dataset(
        self,
        display_name: str,
        query_lines: list[str],
        parameters: Optional[list[dict]] = None,
    ) -> str:
        """Add a dataset and return its name (ID) for use in widgets."""
        name = _hex_id()
        ds: dict[str, Any] = {
            "name": name,
            "displayName": display_name,
            "queryLines": query_lines,
        }
        if parameters:
            ds["parameters"] = parameters
        self.datasets.append(ds)
        return name

    def add_page(self, display_name: str = "Overview") -> PageBuilder:
        page = PageBuilder(_hex_id(), display_name)
        self.pages.append(page)
        return page

    def to_dict(self) -> dict:
        return {
            "datasets": self.datasets,
            "pages": [p.to_dict() for p in self.pages],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        print(f"Dashboard JSON saved to {path}")


# ─── Quick test ────────────────────────────────────────────────────
if __name__ == "__main__":
    db = DashboardBuilder("Sales Dashboard")
    ds = db.add_dataset("Sales Data", [
        "SELECT product, SUM(revenue) as rev, COUNT(*) as orders\n",
        "FROM catalog.schema.sales\n",
        "GROUP BY product\n",
    ])
    pg = db.add_page("Overview")
    pg.add_counter(ds, "rev", title="Total Revenue", position=(0, 0, 2, 2))
    pg.add_counter(ds, "orders", title="Total Orders", transform="SUM", position=(2, 0, 2, 2))
    pg.add_bar(ds, x="product", y="rev", title="Revenue by Product", position=(0, 2, 6, 5))
    pg.add_table(ds, ["product", "rev", "orders"], title="Details", position=(0, 7, 6, 5))

    print(db.to_json())
