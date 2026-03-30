# Integration Guide — DeepAgents (LangChain)

## Overview

This guide shows how to integrate the Databricks Dashboard skill into a
LangChain DeepAgents framework. The skill acts as a **tool** that an agent
can invoke to create dashboards from natural language or SQL queries.

## Architecture

```
User Request (natural language)
    │
    ▼
┌─────────────────────────────────┐
│  DeepAgent (LangChain)          │
│  ┌───────────────────────────┐  │
│  │ 1. StorytellingAnalyzer   │  │ ← Analyze intent, detect story type
│  │    (uses storytelling_    │  │
│  │     framework.md)         │  │
│  ├───────────────────────────┤  │
│  │ 2. DashboardDesigner      │  │ ← Select charts, plan layout
│  │    (uses chart_type_      │  │
│  │     mapping.md)           │  │
│  ├───────────────────────────┤  │
│  │ 3. JSONBuilder            │  │ ← Generate serialized_dashboard
│  │    (uses schema_          │  │
│  │     reference.md +        │  │
│  │     build_dashboard_      │  │
│  │     json.py)              │  │
│  ├───────────────────────────┤  │
│  │ 4. Deployer               │  │ ← Create + Publish via API
│  │    (uses create/publish   │  │
│  │     scripts)              │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
    │
    ▼
Databricks AI/BI Dashboard (live)
```

## Tool Definition Example

```python
from langchain_core.tools import tool
from databricks.sdk import WorkspaceClient
from scripts.build_dashboard_json import DashboardBuilder
from scripts.create_dashboard import create_dashboard
from scripts.publish_dashboard import publish_dashboard
import json


@tool
def create_databricks_dashboard(
    name: str,
    description: str,
    sql_queries: list[dict],
    warehouse_id: str,
    story_type: str = "overview",
) -> dict:
    """
    Create and publish a Databricks AI/BI dashboard.

    Args:
        name: Dashboard display name
        description: What story should this dashboard tell?
        sql_queries: List of {"name": str, "sql": str} dicts
        warehouse_id: Databricks SQL warehouse ID
        story_type: One of: overview, trend, comparison, funnel, geographic, financial, operational

    Returns:
        dict with dashboard_id and published URL
    """
    # 1. Build dashboard JSON
    db = DashboardBuilder(name)

    for q in sql_queries:
        lines = [line + "\n" for line in q["sql"].split("\n") if line.strip()]
        db.add_dataset(q["name"], lines)

    # 2. Design layout based on story type
    # (Agent should populate this based on storytelling_framework.md)
    pg = db.add_page("Overview")
    # ... agent adds widgets here based on analysis ...

    # 3. Create dashboard
    serialized = db.to_json()
    result = create_dashboard(
        name=name,
        serialized_dashboard_json=serialized,
        warehouse_id=warehouse_id,
    )

    # 4. Publish
    pub = publish_dashboard(
        dashboard_id=result.dashboard_id,
        warehouse_id=warehouse_id,
    )

    return {
        "dashboard_id": result.dashboard_id,
        "path": result.path,
        "status": "published",
    }
```

## Agent System Prompt Integration

When using this skill in a DeepAgent, include these instructions in the agent's
system prompt or tool description:

```
You have access to a Databricks Dashboard creation skill. When the user asks
to create a dashboard:

1. FIRST read references/storytelling_framework.md to determine the story type
2. THEN read references/chart_type_mapping.md to select appropriate charts
3. Use scripts/build_dashboard_json.py (DashboardBuilder) to construct the JSON
4. Deploy via scripts/create_dashboard.py and scripts/publish_dashboard.py

ALWAYS follow the storytelling-first approach:
- Identify what story the data tells BEFORE choosing chart types
- Start with Counters (KPIs) at the top
- Place the hero chart (main story) prominently
- End with detail tables at the bottom
- Use filters for interactivity
```

## Multi-Step Agent Flow

For complex dashboards, the agent should work in steps:

### Step 1: Story Analysis
```python
# Agent analyzes user request + SQL queries
story_analysis = {
    "primary_story": "trend",
    "secondary_stories": ["comparison", "composition"],
    "audience": "executives",
    "key_metrics": ["revenue", "order_count", "avg_order_value"],
    "dimensions": ["product_category", "order_date", "region"],
    "filters_needed": ["product_category", "date_range"],
}
```

### Step 2: Dashboard Design
```python
# Agent creates a design plan
design_plan = {
    "pages": [
        {
            "name": "Overview",
            "widgets": [
                {"type": "filter-date-range-picker", "field": "order_date", "pos": (0, 0, 2, 1)},
                {"type": "filter-multi-select", "field": "product_category", "pos": (2, 0, 2, 1)},
                {"type": "counter", "metric": "revenue", "title": "Total Revenue", "pos": (0, 1, 2, 2)},
                {"type": "counter", "metric": "order_count", "title": "Orders", "pos": (2, 1, 2, 2)},
                {"type": "counter", "metric": "avg_order_value", "title": "AOV", "pos": (4, 1, 2, 2)},
                {"type": "line", "x": "order_date", "y": "revenue", "color": "product_category",
                 "title": "Revenue Trend", "pos": (0, 3, 6, 6)},
                {"type": "bar", "x": "product_category", "y": "revenue",
                 "title": "Revenue by Category", "pos": (0, 9, 3, 5)},
                {"type": "pie", "angle": "order_count", "color": "product_category",
                 "title": "Order Distribution", "pos": (3, 9, 3, 5)},
                {"type": "table", "columns": ["order_id", "customer", "product", "revenue", "date"],
                 "title": "Recent Orders", "pos": (0, 14, 6, 6)},
            ]
        }
    ]
}
```

### Step 3: Build & Deploy
```python
# Agent uses DashboardBuilder to construct JSON and deploy
db = DashboardBuilder("Sales Dashboard")
# ... builds from design_plan ...
result = create_dashboard(...)
publish_dashboard(...)
```

## Environment Setup

```bash
# Required
pip install databricks-sdk

# Environment variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi..."

# Or use service principal
export DATABRICKS_CLIENT_ID="..."
export DATABRICKS_CLIENT_SECRET="..."
```
