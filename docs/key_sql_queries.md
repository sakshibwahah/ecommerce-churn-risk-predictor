# Key SQL Queries

All queries run against `data/olist.db` (SQLite). Connect via:
```python
from sqlalchemy import create_engine
engine = create_engine('sqlite:///data/olist.db')
df = pd.read_sql(query, engine)
```

---

## 1. Revenue by State

```sql
SELECT 
    c.customer_state,
    ROUND(SUM(op.payment_value), 2)      AS total_revenue,
    COUNT(DISTINCT o.order_id)           AS total_orders,
    ROUND(AVG(op.payment_value), 2)      AS avg_order_value,
    COUNT(DISTINCT o.customer_id)        AS unique_customers
FROM orders o
JOIN customers c  ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;
```

---

## 2. Delivery Performance Analysis

```sql
SELECT
    order_id,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    -- Delay in days (positive = late, negative = early)
    JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_estimated_delivery_date) AS delay_days,
    -- Actual transit time
    JULIANDAY(order_delivered_customer_date) - JULIANDAY(order_purchase_timestamp)       AS transit_days,
    CASE 
        WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 1 
        ELSE 0 
    END AS on_time
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL;
```

---

## 3. Monthly Order & Revenue Trend

```sql
SELECT
    STRFTIME('%Y-%m', order_purchase_timestamp) AS month,
    COUNT(*)                                     AS num_orders,
    COUNT(DISTINCT customer_id)                  AS unique_customers,
    ROUND(SUM(payment_value), 2)                 AS monthly_revenue
FROM orders o
JOIN order_payments op ON o.order_id = op.order_id
WHERE order_status NOT IN ('canceled', 'unavailable')
  AND order_purchase_timestamp >= '2017-01-01'
GROUP BY month
ORDER BY month;
```

---

## 4. RFM Base Query (per customer)

```sql
SELECT
    o.customer_id,
    MAX(o.order_purchase_timestamp)            AS last_purchase,
    COUNT(DISTINCT o.order_id)                 AS frequency,
    ROUND(SUM(op.payment_value), 2)            AS monetary,
    MIN(o.order_purchase_timestamp)            AS first_purchase,
    -- Recency in days from reference date (computed in Python)
    JULIANDAY('2018-09-04') - JULIANDAY(MAX(o.order_purchase_timestamp)) AS recency_days
FROM orders o
JOIN order_payments op ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY o.customer_id;
```

---

## 5. Churn Feature Engineering (per customer)

```sql
SELECT 
    o.customer_id,
    o.order_id,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    o.order_status,
    op.payment_value,
    r.review_score,
    r.review_comment_message,
    c.customer_state,
    -- Delivery delay per order
    JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date) AS delivery_delay_days
FROM orders o
JOIN customers c         ON o.customer_id = c.customer_id
JOIN order_payments op   ON o.order_id = op.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered';
```

---

## 6. State-Level Delivery & Revenue Summary

```sql
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id)                                                AS total_orders,
    ROUND(AVG(
        CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date 
             THEN JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date)
             ELSE 0 END
    ), 2)                                                                     AS avg_delay_days,
    ROUND(AVG(
        CASE WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date 
             THEN 1.0 ELSE 0.0 END
    ), 4)                                                                     AS on_time_rate,
    ROUND(SUM(op.payment_value), 2)                                          AS total_revenue,
    ROUND(AVG(r.review_score), 2)                                            AS avg_review_score
FROM orders o
JOIN customers c         ON o.customer_id = c.customer_id
JOIN order_payments op   ON o.order_id = op.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY total_revenue DESC;
```

---

## 7. Review Score vs Delivery Delay

```sql
SELECT
    r.review_score,
    COUNT(*)                                                                         AS review_count,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date)
    ), 2)                                                                            AS avg_delay_days,
    ROUND(SUM(op.payment_value), 2)                                                  AS total_revenue
FROM order_reviews r
JOIN orders o            ON r.order_id = o.order_id
JOIN order_payments op   ON o.order_id = op.order_id
WHERE o.order_status = 'delivered'
GROUP BY r.review_score
ORDER BY r.review_score;
```

---

## 8. Top Product Categories by Revenue

```sql
SELECT
    COALESCE(ct.product_category_name_english, p.product_category_name) AS category,
    ROUND(SUM(oi.price), 2)              AS total_revenue,
    COUNT(DISTINCT oi.order_id)          AS order_count,
    ROUND(AVG(oi.price), 2)             AS avg_item_price,
    ROUND(AVG(oi.freight_value), 2)     AS avg_freight
FROM order_items oi
JOIN products p               ON oi.product_id = p.product_id
LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
GROUP BY category
ORDER BY total_revenue DESC
LIMIT 20;
```

---

## 9. Seller Performance Ranking

```sql
SELECT
    oi.seller_id,
    s.seller_state,
    COUNT(DISTINCT oi.order_id)          AS total_orders,
    ROUND(SUM(oi.price), 2)             AS total_revenue,
    ROUND(AVG(r.review_score), 2)       AS avg_review_score,
    ROUND(AVG(
        JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date)
    ), 2)                               AS avg_delay_days
FROM order_items oi
JOIN sellers s        ON oi.seller_id = s.seller_id
JOIN orders o         ON oi.order_id = o.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY oi.seller_id, s.seller_state
HAVING total_orders >= 10
ORDER BY avg_review_score ASC
LIMIT 20;
```

---

## 10. High-Value Churned Customers (At-Risk Target List)

```sql
-- Run after churn_predictions.csv is merged back into SQLite
-- This is conceptual: combine Python-computed churn_prob with SQL
SELECT 
    o.customer_id,
    c.customer_state,
    COUNT(DISTINCT o.order_id)          AS num_orders,
    ROUND(SUM(op.payment_value), 2)    AS total_spent,
    MAX(o.order_purchase_timestamp)    AS last_order_date,
    ROUND(AVG(r.review_score), 2)      AS avg_review
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY o.customer_id
HAVING total_spent > 300
   AND JULIANDAY('2018-09-04') - JULIANDAY(MAX(o.order_purchase_timestamp)) > 180
ORDER BY total_spent DESC
LIMIT 50;
```
