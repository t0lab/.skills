"""
publish_dashboard.py — Publish a draft Databricks AI/BI dashboard.

Prerequisites:
    pip install databricks-sdk

Usage (CLI):
    python publish_dashboard.py \
        --dashboard-id "04aab30f99ea444490c10c85852f216c" \
        --warehouse-id "abc123def456" \
        --embed-credentials

Usage (as module):
    from publish_dashboard import publish_dashboard
    publish_dashboard(
        dashboard_id="04aab30f99ea...",
        warehouse_id="abc123def456",
        embed_credentials=True,
    )
"""

from __future__ import annotations

import argparse
import json

from databricks.sdk import WorkspaceClient


def publish_dashboard(
    dashboard_id: str,
    warehouse_id: str | None = None,
    embed_credentials: bool = True,
    workspace_client: WorkspaceClient | None = None,
) -> dict:
    """
    Publish a draft dashboard to make it accessible.

    Args:
        dashboard_id: The UUID of the draft dashboard.
        warehouse_id: Optional warehouse override for the published version.
        embed_credentials: Embed publisher's credentials (default True).
        workspace_client: Optional pre-configured WorkspaceClient.

    Returns:
        Published dashboard metadata.
    """
    w = workspace_client or WorkspaceClient()

    result = w.lakeview.publish(
        dashboard_id=dashboard_id,
        warehouse_id=warehouse_id,
        embed_credentials=embed_credentials,
    )

    print(f"✅ Dashboard published successfully!")
    print(f"   Dashboard ID: {dashboard_id}")
    if warehouse_id:
        print(f"   Warehouse:    {warehouse_id}")
    print(f"   Credentials:  {'embedded' if embed_credentials else 'viewer credentials'}")

    return {
        "dashboard_id": dashboard_id,
        "status": "published",
        "embed_credentials": embed_credentials,
    }


def get_published_url(host: str, dashboard_id: str) -> str:
    """Construct the URL for a published dashboard."""
    host = host.rstrip("/")
    return f"{host}/dashboardsv3/{dashboard_id}/published"


def main():
    parser = argparse.ArgumentParser(description="Publish a Databricks AI/BI dashboard")
    parser.add_argument("--dashboard-id", required=True, help="Dashboard UUID")
    parser.add_argument("--warehouse-id", default=None, help="SQL warehouse ID override")
    parser.add_argument(
        "--embed-credentials",
        action="store_true",
        default=True,
        help="Embed publisher credentials (default: True)",
    )
    parser.add_argument(
        "--no-embed-credentials",
        action="store_true",
        help="Use viewer credentials instead",
    )

    args = parser.parse_args()

    embed = not args.no_embed_credentials

    result = publish_dashboard(
        dashboard_id=args.dashboard_id,
        warehouse_id=args.warehouse_id,
        embed_credentials=embed,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
