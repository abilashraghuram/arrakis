---
name: data-analysis
description: Analyze datasets using pandas, generate reports, and create visualizations
version: 1.0.0
author: cintegrity
---

# Data Analysis Skill

Expert guidance for analyzing datasets, generating insights, and creating reports.

## Analysis Approach

When analyzing data, follow this systematic approach:

1. **Understand the question** - What specific insight is needed?
2. **Load and inspect** - Get the data, check columns, row counts, data types
3. **Aggregate and query** - Group, sum, filter to answer the question
4. **Format results** - Present findings clearly with context
5. **Save deliverables** - Output reports in the requested format

## Common Analysis Patterns

### Revenue/Sales Analysis
- Group by region, product, time period
- Calculate totals, averages, percentages
- Compare across dimensions

### Data Quality Checks
- Count missing values per column
- Identify outliers (values > 3 std from mean)
- Check for duplicates

### Time Series
- Group by date/month/quarter
- Calculate period-over-period changes
- Identify trends and seasonality

## Report Structure

A good analysis report includes:

```
# [Title]

## Summary
- Key finding 1
- Key finding 2

## Details
[Breakdown by dimension with numbers]

## Methodology
[Brief description of approach]
```

## Workflow Templates

See `scripts/analyze_csv.py` for a reusable workflow pattern.
See `references/examples.md` for common query patterns.
