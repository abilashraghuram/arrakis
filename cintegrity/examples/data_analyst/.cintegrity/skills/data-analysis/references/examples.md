# Data Analysis - Query Patterns

Common query patterns for data analysis tasks.

## Aggregation Queries

### Sum by Dimension
```sql
SELECT region, SUM(revenue) as total_revenue
FROM sales
GROUP BY region
```

### Average with Count
```sql
SELECT category, AVG(price) as avg_price, COUNT(*) as count
FROM products
GROUP BY category
```

### Top N by Metric
```sql
SELECT product, SUM(units_sold) as total_units
FROM sales
GROUP BY product
ORDER BY total_units DESC
LIMIT 10
```

## Time-Based Analysis

### Monthly Totals
```sql
SELECT DATE_TRUNC('month', date) as month, SUM(revenue)
FROM sales
GROUP BY month
ORDER BY month
```

### Year-over-Year Comparison
```sql
SELECT
  EXTRACT(YEAR FROM date) as year,
  SUM(revenue) as total_revenue
FROM sales
GROUP BY year
```

## Filtering Patterns

### Date Range
```sql
SELECT * FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
```

### Multiple Conditions
```sql
SELECT * FROM customers
WHERE region = 'North' AND lifetime_value > 10000
```

## Report Formatting

### Revenue by Region Report
```
# Q4 Sales Analysis

## Revenue by Region
- North: $1,250,000.00
- South: $890,000.50
- East: $1,100,000.00
- West: $1,010,000.00

## Total: $4,250,000.50
```

### Summary Statistics Report
```
# Dataset Summary

## Overview
- Total Rows: 15,000
- Columns: date, product, region, revenue, units

## Key Metrics
- Total Revenue: $4.25M
- Average Order: $283.33
- Top Region: North (29.4%)
```
