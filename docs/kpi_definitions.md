# KPI Definitions

This document defines all Key Performance Indicators (KPIs) used in the Olist Churn Analytics dashboard and notebooks.

---

## 1. Churn Rate

**Definition:** Percentage of customers who have not placed a new order within a 180-day window after their last recorded purchase.

**Formula:**
```
Churn Rate = (# customers with recency > 180 days) / (total unique customers) × 100
```

**Data Source:** `orders.order_purchase_timestamp` per `customer_id`

**Reference Date:** 1 day after the maximum `order_purchase_timestamp` in the dataset (2018-09-04 for the Olist dataset).

**Industry Benchmark:** E-commerce churn rates typically range from 15–30% annually. Olist's single-purchase rate is much higher due to marketplace dynamics.

**Threshold:** A customer with `churn_prob > 0.5` from the XGBoost model is classified as "at-risk".

---

## 2. Revenue at Risk (BRL)

**Definition:** The estimated future revenue that would be lost if a high-churn-probability customer stops purchasing.

**Formula:**
```
Revenue at Risk = CLV × P(churn)     [per customer]
Total Revenue at Risk = Σ(CLV_i × P(churn)_i)    [across all customers]
```

**Data Source:** `order_payments.payment_value`, XGBoost churn probability score

**Interpretation:** A customer with CLV = R$500 and P(churn) = 0.80 contributes R$400 to revenue at risk.

---

## 3. Customer Lifetime Value (CLV)

**Definition:** Estimated total revenue a customer will generate over their entire relationship with Olist.

**Formula:**
```
CLV = Average Order Value × Purchase Frequency × Customer Lifespan

Where:
  Average Order Value   = Total Payment Value / Number of Orders
  Purchase Frequency    = Number of Orders / Observation Period (months)
  Customer Lifespan     = 24 months (industry standard for e-commerce)
  Observation Period    = 18 months (Sep 2016 – Mar 2018)
```

**Data Source:** `order_payments.payment_value`, `orders.order_id` per `customer_id`

**Note:** CLV is forward-looking. The 24-month lifespan is a conservative estimate for Brazilian e-commerce. Adjust based on your cohort analysis.

---

## 4. On-Time Delivery Rate

**Definition:** Percentage of delivered orders that arrived on or before the estimated delivery date.

**Formula:**
```
On-Time Rate = (# orders where delivered_date ≤ estimated_date) / (# delivered orders) × 100
```

**Data Source:** `orders.order_delivered_customer_date`, `orders.order_estimated_delivery_date`

**Filter:** Only `order_status = 'delivered'` orders with non-null delivery dates.

**Target:** ≥ 92% (industry benchmark for e-commerce fulfilment).

---

## 5. Average Review Score

**Definition:** Mean customer review score across all delivered orders.

**Formula:**
```
Avg Review Score = Mean(review_score) for all delivered orders
```

**Scale:** 1 (very dissatisfied) to 5 (very satisfied)

**Data Source:** `order_reviews.review_score`

**Insight:** Review score correlates negatively with churn. Customers giving 1–2 star reviews have a significantly higher churn probability (SHAP analysis confirms this).

---

## 6. Delivery Delay (days)

**Definition:** Number of days an order arrived after (positive) or before (negative) the estimated delivery date.

**Formula:**
```
Delay Days = JULIANDAY(delivered_date) - JULIANDAY(estimated_date)
```

**Positive = Late, Negative = Early**

**Data Source:** `orders` table

**Key Insight:** Each additional day of delay increases churn probability by approximately 3–5% (from SHAP feature importance analysis).

---

## 7. RFM Scores

### Recency (R)
- Days since the customer's most recent order
- Scored 1–5: 5 = most recent (lowest recency days)

### Frequency (F)
- Total number of distinct orders placed by the customer
- Scored 1–5: 5 = highest frequency

### Monetary (M)
- Total payment value across all orders (BRL)
- Scored 1–5: 5 = highest spender

### RFM Segment Labels

| Segment | R | F | M | Description |
|---------|---|---|---|-------------|
| Champions | ≥4 | ≥4 | ≥4 | Best customers, bought recently, often, and spent most |
| Loyal Customers | ≥3 | ≥3 | any | Regular buyers, strong engagement |
| Potential Loyalists | ≥3 | ≤2 | ≥3 | Recent + high-value, not yet frequent |
| Recent Customers | ≥4 | ≤2 | any | Just bought, not yet loyal |
| At Risk | 2 | ≥3 | any | Used to buy often but haven't recently |
| Can't Lose Them | ≤2 | ≤2 | ≥3 | High-value but going cold |
| Hibernating | ≤2 | ≥3 | any | Low recent activity, used to be frequent |
| Lost | ≤2 | ≤2 | ≤2 | Last purchase was long ago, low value/frequency |
| Need Attention | all others | — | — | Borderline, require monitoring |

---

## 8. SHAP (SHapley Additive exPlanations)

**Definition:** A game-theory-based method that assigns each feature an importance value for a specific prediction. Positive SHAP values push toward churn; negative values push against churn.

**Formula (Shapley Value):**
```
φ_i = Σ (|S|! × (|F|-|S|-1)! / |F|!) × [f(S∪{i}) - f(S)]
```

**Top Features (expected ranking by SHAP importance):**
1. `recency_days` — most predictive of churn
2. `delivery_delay_days` — operational lever
3. `avg_review_score` — satisfaction signal
4. `avg_sentiment` — NLP signal from review comments
5. `R` (RFM Recency score) — correlated with recency_days
6. `num_orders` / `F` — engagement depth
7. `total_payment_value` / `M` — customer value
