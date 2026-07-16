# KPI Definitions

This document defines all Key Performance Indicators (KPIs) used in the Olist Churn Analytics dashboard and notebooks.

---

## 1. Churn Rate

**Definition:** Percentage of orders that resulted in a **dissatisfied experience**, defined as a review score of 1 or 2. This framing is used because the Olist dataset assigns a new `customer_id` per transaction, making recency-based churn definitions unreliable (they produce near-100% churn rates by construction).

**Formula:**
```
Churn Rate = (# orders with review_score ≤ 2) / (total orders with a review) × 100
```

**Data Source:** `order_reviews.review_score` joined to `orders`

**Why not recency-based?** Defining churn as "no order in 180 days" and including `recency_days` as a model feature causes AUC = 1.0 (direct label leakage — the feature encodes the label boundary). The dissatisfied-experience definition eliminates this entirely.

**Industry Benchmark:** A 12–15% dissatisfied-order rate is typical in e-commerce marketplaces with mixed seller quality.

**Threshold:** An order with `churn_prob > 0.5` from the XGBoost model is classified as high-risk.

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

**Top Features (actual ranking by SHAP importance for this model):**
1. `delivery_delay_days` — primary driver; each extra day of delay strongly increases dissatisfaction probability
2. `actual_delivery_days` — absolute time perception, independent of the estimated date
3. `review_vader_score` — VADER compound sentiment on review comment text (Portuguese lexicon injected)
4. `freight_ratio` — disproportionate shipping cost relative to item price creates frustration
5. `price` — higher-value orders have greater expectation and higher churn sensitivity
6. `category_enc` — certain categories (electronics, large furniture) have structurally higher dispute rates
7. `customer_state_enc` — regional delivery infrastructure varies; northern states see higher delays
8. `same_state` — cross-state logistics are slower and more likely to arrive late
9. `product_photos_qty` — low-quality listings lead to expectation mismatch
10. `description_length` — short descriptions correlate with information asymmetry and returns
