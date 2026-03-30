"""
create_dashboard.py — Create a Databricks AI/BI dashboard via WorkspaceClient.

Prerequisites:
    pip install databricks-sdk

Authentication:
    Uses databricks-sdk unified auth. Set environment variables:
    - DATABRICKS_HOST
    - DATABRICKS_TOKEN
    Or use ~/.databrickscfg profile, or Azure/GCP service principal.

Usage (CLI):
    python create_dashboard.py \
        --name "My Dashboard" \
        --warehouse-id "abc123def456" \
        --json-path ./dashboard.json \
        --parent-path "/Users/user@example.com/dashboards"

Usage (as module):
    from create_dashboard import create_dashboard
    result = create_dashboard(
        name="My Dashboard",
        serialized_dashboard_json='{"pages": [...]}',
        warehouse_id="abc123def456",
    )
    print(result.dashboard_id)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import Dashboard


def create_dashboard(
    name: str,
    serialized_dashboard_json: str,
    warehouse_id: str,
    parent_path: str | None = None,
    workspace_client: WorkspaceClient | None = None,
) -> Dashboard:
    """
    Create a draft AI/BI dashboard.

    Args:
        name: Display name of the dashboard.
        serialized_dashboard_json: JSON string of the serialized_dashboard payload.
        warehouse_id: SQL warehouse ID to execute queries.
        parent_path: Workspace folder path. Defaults to user's home.
        workspace_client: Optional pre-configured WorkspaceClient.

    Returns:
        Dashboard object with dashboard_id and metadata.
    """
    w = workspace_client or WorkspaceClient()

    dashboard = Dashboard(
        display_name=name,
        warehouse_id=warehouse_id,
        serialized_dashboard=serialized_dashboard_json,
        parent_path=parent_path,
    )

    result = w.lakeview.create(dashboard=dashboard)

    print(f"✅ Dashboard created successfully!")
    print(f"   ID:   {result.dashboard_id}")
    print(f"   Name: {result.display_name}")
    print(f"   Path: {result.path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Create a Databricks AI/BI dashboard")
    parser.add_argument("--name", required=True, help="Dashboard display name")
    parser.add_argument("--warehouse-id", required=True, help="SQL warehouse ID")
    parser.add_argument("--json-path", required=True, help="Path to serialized_dashboard JSON file")
    parser.add_argument("--parent-path", default=None, help="Workspace folder path (optional)")

    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"❌ File not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        dashboard_dict = json.load(f)

    serialized = json.dumps(dashboard_dict, ensure_ascii=False)

    result = create_dashboard(
        name=args.name,
        serialized_dashboard_json=serialized,
        warehouse_id=args.warehouse_id,
        parent_path=args.parent_path,
    )

    # Output result as JSON for downstream consumption
    print(json.dumps({
        "dashboard_id": result.dashboard_id,
        "display_name": result.display_name,
        "path": result.path,
    }, indent=2))


if __name__ == "__main__":
    main()
