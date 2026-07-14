# Problem Statement

## Background

Olist is a Brazilian e-commerce marketplace that connects small businesses to major retail channels. Between September 2016 and August 2018, Olist processed over **100,000 real orders** across 27 Brazilian states. This dataset, released under CC-BY-NC-SA-4.0, includes orders, customers, payments, product reviews, seller information, and geolocation data.

## Business Problem

Olist faces a **customer retention crisis**: the majority of customers make only **one purchase**, and high delivery delays correlate with poor reviews, product returns, and permanent customer loss. The business lacks:

1. **Visibility** into which customers are most likely to churn
2. **Quantification** of the revenue at risk from churning customers
3. **Segmentation** of customers into actionable groups for targeted interventions
4. **Geospatial understanding** of where churn and delivery failures are concentrated
5. **A simulation tool** to model the ROI of operational improvements (e.g., faster delivery)

## Objectives

| Objective | Method | Outcome |
|-----------|--------|---------|
| Identify churned customers | Time-based churn labelling (no order in 180 days) | Binary churn labels for 90k+ customers |
| Predict churn probability | XGBoost classifier with VADER NLP features | Probability score per customer (AUC-ROC ≥ 0.80) |
| Segment customer base | RFM scoring (Recency, Frequency, Monetary) | 9 actionable segments (Champions → Lost) |
| Quantify revenue at risk | CLV × P(churn) | Total BRL at risk per customer and segment |
| Map delivery & churn | Folium choropleths on Brazilian states | 3 interactive HTML maps |
| Enable intervention modelling | Streamlit Intervention Simulator | Revenue saved per day of delay reduction |

## Dataset

| Table | Rows | Description |
|-------|------|-------------|
| orders | ~99,441 | Order lifecycle (purchased → delivered) |
| order_items | ~112,650 | Products, prices, freight per order |
| order_payments | ~103,886 | Payment type and value |
| order_reviews | ~99,224 | Review score (1–5) + comment text |
| customers | ~99,441 | Customer ID, city, state |
| products | ~32,951 | Product category |
| sellers | ~3,095 | Seller location |
| geolocation | ~1M | ZIP code → lat/lon mapping |

## Success Criteria

- XGBoost churn model achieves **AUC-ROC ≥ 0.80** on held-out test set
- SHAP explanations correctly identify delivery delay and review score as top churn drivers
- Streamlit dashboard loads all 5 tabs without errors on a machine with pre-computed outputs
- Revenue at risk is quantified to **BRL precision** per customer and per segment
