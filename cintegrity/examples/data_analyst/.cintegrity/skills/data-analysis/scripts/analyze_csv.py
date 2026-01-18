"""Data Analysis Workflow Template

Pattern: Load → Query → Format → Save

Adapt tool names to match your available tools (check list_tools output).
"""


def workflow():
    """Analyze dataset and generate report.

    This template demonstrates the standard analysis pattern.
    Modify tool names and parameters to match your environment.
    """
    from cintegrity.tools import load_dataset, query_data, save_report

    # 1. Load the dataset
    dataset = load_dataset(name="sales_2024")
    dataset_name = dataset["name"]
    row_count = dataset["rows"]

    # 2. Query for aggregated data
    result = query_data(
        dataset=dataset_name,
        query="SELECT region, SUM(revenue) as total_revenue GROUP BY region",
    )
    data = result["data"]

    # 3. Format report content
    lines = []
    lines.append("# Sales Analysis Report")
    lines.append("")
    lines.append("## Revenue by Region")

    total = 0
    for row in data:
        region = row["region"]
        revenue = row["total_revenue"]
        total = total + revenue
        line = f"- {region}: ${revenue:,.2f}"
        lines.append(line)

    lines.append("")
    lines.append(f"## Total: ${total:,.2f}")
    lines.append("")
    lines.append(f"_Based on {row_count} records_")

    report = "\n".join(lines)

    # 4. Save the report
    save_result = save_report(filename="q4_analysis.txt", content=report)

    return save_result
