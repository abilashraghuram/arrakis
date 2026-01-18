"""Mock data tools for the data analyst example."""

from typing import Any, TypedDict

# --- Tool Argument Types ---


class LoadDatasetArgs(TypedDict):
    name: str


class QueryDataArgs(TypedDict):
    dataset: str
    query: str


class SaveReportArgs(TypedDict):
    filename: str
    content: str


# --- Tool Output Types ---


class DatasetInfo(TypedDict):
    name: str
    rows: int
    columns: list[str]
    sample: Any  # list of row dicts


class QueryResult(TypedDict):
    success: bool
    data: Any  # list of result dicts
    row_count: int


class SaveResult(TypedDict):
    success: bool
    path: str


# --- Mock Tools ---


def load_dataset(args: LoadDatasetArgs) -> DatasetInfo:
    """Load a dataset by name.

    Returns dataset info with name, row count, columns, and sample data.
    """
    # Mock datasets
    datasets = {
        "sales_2024": {
            "name": "sales_2024",
            "rows": 15000,
            "columns": ["date", "product", "region", "revenue", "units"],
            "sample": [
                {
                    "date": "2024-01-15",
                    "product": "Widget A",
                    "region": "North",
                    "revenue": 1250.00,
                    "units": 50,
                },
                {
                    "date": "2024-01-16",
                    "product": "Widget B",
                    "region": "South",
                    "revenue": 890.50,
                    "units": 30,
                },
                {
                    "date": "2024-01-17",
                    "product": "Widget A",
                    "region": "East",
                    "revenue": 2100.00,
                    "units": 84,
                },
            ],
        },
        "customers": {
            "name": "customers",
            "rows": 5000,
            "columns": ["id", "name", "email", "segment", "lifetime_value"],
            "sample": [
                {
                    "id": "C001",
                    "name": "Acme Corp",
                    "email": "contact@acme.com",
                    "segment": "Enterprise",
                    "lifetime_value": 125000,
                },
                {
                    "id": "C002",
                    "name": "StartupXYZ",
                    "email": "hello@startup.xyz",
                    "segment": "SMB",
                    "lifetime_value": 8500,
                },
            ],
        },
    }

    name = args["name"]
    if name in datasets:
        return datasets[name]

    return {
        "name": name,
        "rows": 0,
        "columns": [],
        "sample": [],
    }


def query_data(args: QueryDataArgs) -> QueryResult:
    """Run a query against a loaded dataset.

    Returns query results with success status, data rows, and row count.
    """
    print(f"  [MOCK] Running query on {args['dataset']}: {args['query']}")

    # Mock query results - always return region breakdown for this example
    return {
        "success": True,
        "data": [
            {"region": "North", "total_revenue": 1250000.00},
            {"region": "South", "total_revenue": 890000.50},
            {"region": "East", "total_revenue": 1100000.00},
            {"region": "West", "total_revenue": 1010000.00},
        ],
        "row_count": 4,
    }


def save_report(args: SaveReportArgs) -> SaveResult:
    """Save analysis report to a file.

    Returns success status and file path.
    """
    print(f"  [MOCK] Saving report to {args['filename']}")
    return {
        "success": True,
        "path": f"/reports/{args['filename']}",
    }


# Export all tools
TOOLS = [load_dataset, query_data, save_report]
