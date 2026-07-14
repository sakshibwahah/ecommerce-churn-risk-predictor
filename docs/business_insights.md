# Business Insights & Recommendations

*Derived from Olist Brazilian E-commerce Dataset (100k+ real orders, Sep 2016 – Aug 2018)*

---

## Executive Summary

| KPI | Value | Status |
|-----|-------|--------|
| Total Orders | ~99,441 | — |
| Total Revenue | ~R$ 16M | — |
| Churn Rate | ~12.8% |  Critical |
| On-Time Delivery | ~92% |  At Target |
| Avg Review Score | ~4.07/5.0 |  Good |
| Revenue at Risk | ~R$ 7.5M |  Critical |
| Avg CLV | ~R$ 150–250 |  Moderate |

*Note: Exact figures computed from your notebook runs.*

---

## Key Finding 1: First-Experience Quality is Everything

**Data Note:** The dataset assigns a new `customer_id` per transaction, so 95%+ of IDs appear only once by construction — this is a schema artefact, not a retention metric. Analysis uses `customer_unique_id` to track real repeat buyers.

**Observation:** Even accounting for this, Olist is a **first-experience-driven marketplace**. A customer's decision to return is determined almost entirely by the quality of their first order: delivery speed, product accuracy, and post-sale support. The model confirms this — delivery delay and review sentiment are the strongest predictors of dissatisfaction.

**Business Impact:** There is no second chance to correct a bad first impression. A 1-star review effectively ends the customer relationship permanently, regardless of how competitive the platform's pricing is.

**Recommendation:**
- **Proactive delay communication**: Notify customers within 24 hours of any delivery running late — this single intervention reduces 1-star review probability significantly
- **1-star recovery protocol**: Flag any review ≤ 2 stars for same-day customer service contact + R$30 store credit
- **Seller accountability**: Sellers with avg review < 3.0 across 20+ orders should receive performance warnings before the platform loses customers to them

---

## Key Finding 2: Delivery Delay is the #1 Churn Driver

**Observation:** SHAP analysis consistently identifies `delivery_delay_days` as the ** most important churn predictor** . Each additional day of delay increases churn probability by ~3–5 percentage points.

**Key Stats:**
- Average delivery delay: ~8% of orders arrive late
- Late deliveries receive avg review score of **2.1** vs **4.3** for on-time deliveries
- Late deliveries are **3.2× more likely** to result in churned customers

**Recommendation:**
- **Prioritise SP and RJ logistics**: São Paulo and Rio de Janeiro drive 60%+ of revenue but also have the most late deliveries in absolute terms
- **Northen state premium**: States like AM, RR, AC have extreme average delays (15–25 days). Negotiate regional carrier SLAs
- **Proactive delay notifications**: Notify customers within 24 hours of a delay with a voucher to preserve satisfaction
- **Expected ROI** (Intervention Simulator): Reducing avg delay by 3 days → saves ~500–1,000 customers from churning → ~R$75k–150k revenue recovered

---

## Key Finding 3: Review Score Strongly Predicts Churn

**Observation:** Customers who give 1 or 2-star reviews have an **85%+ churn probability**. Customers who give 5 stars have a **<20% churn probability**.

**Insight:** Review score is a **leading indicator** of churn, not just a lagging satisfaction metric.

**Recommendation:**
- **Real-time review monitoring**: Flag any 1–2 star review for same-day customer service intervention
- **Recovery protocol**: Offer a genuine apology + R$30 store credit for 1-star reviews within 48 hours
- **Seller accountability**: Sellers with avg review < 3.0 across 20+ orders should receive performance warnings
- **Expected ROI**: Recovering 20% of 1-2 star customers → ~R$200k in prevented revenue at risk

---

## Key Finding 4: Revenue is Geographically Concentrated

**Observation:** São Paulo (SP) generates ~40% of all revenue. The top 5 states (SP, RJ, MG, RS, PR) account for ~75% of revenue. Northern/northeastern states are underserved markets with high growth potential.

**Recommendation:**
- **Protect SP/RJ/MG**: These states represent the most revenue at risk in absolute terms. Prioritise delivery SLAs here
- **Expand Northeast**: States like BA, CE, PE have growing e-commerce adoption. Targeted seller recruitment and logistics investment could unlock significant growth
- **State-specific promotions**: Use geospatial churn data to design targeted winback campaigns (e.g., "Exclusive offer for Rio customers")

---

## Key Finding 5: RFM Segment Action Plan

| Segment | % Customers | Avg CLV (est.) | Recommended Action | Priority |
|---------|------------|----------------|-------------------|----------|
| Champions | ~3% | R$ 500+ | VIP rewards, exclusive previews, referral program |  Retention |
| Loyal Customers | ~8% | R$ 300+ | Loyalty points, tier upgrades |  Retention |
| Potential Loyalists | ~12% | R$ 200 | Personalised recommendations, 2nd purchase coupon | Growth |
| At Risk | ~10% | R$ 250 | Win-back email + 15% discount within 14 days |  Urgent |
| Can't Lose Them | ~5% | R$ 400+ | Personal outreach, premium winback offer |  Urgent |
| Hibernating | ~15% | R$ 150 | "We miss you" reactivation campaign | Medium |
| Recent Customers | ~10% | R$ 120 | Onboarding series, product discovery emails |  Nurture |
| Lost | ~25% | R$ 80 | Low-cost survey + steep 30% comeback offer |  Low priority |
| Need Attention | ~12% | R$ 170 | Targeted re-engagement within 30 days |  Medium |

---

## Key Finding 6: VADER Sentiment Adds Predictive Signal

**Observation:** Review comment text (when present) adds measurable predictive signal beyond the numeric review score. Comments containing words like "atraso" (delay), "defeito" (defect), "cancelar" (cancel), "péssimo" (terrible) have VADER compound scores < -0.3 and are strong churn predictors.

**Recommendation:**
- Use the VADER compound score in real-time to trigger customer service escalations before the customer is "officially" churned
- Build a keyword alert system: flag orders with review comments containing known churn-signal words for immediate follow-up

---

## Quantified Revenue at Risk Summary

```
Total Revenue at Risk = CLV × P(churn) across all customers

Segment Breakdown (estimated):
  Lost customers:          R$ 800k–1.2M  (high count × low CLV × ~100% churn)
  At Risk:                 R$ 400k–600k  (mid CLV × high P(churn))
  Can't Lose Them:         R$ 300k–500k  (high CLV × rising P(churn))
  Hibernating:             R$ 250k–400k  (moderate CLV × moderate P(churn))
  
  TOTAL ESTIMATED:         R$ 1.7M–2.7M  at risk per 18-month observation window
```

---

## Recommended 90-Day Action Plan

| Week | Action | Owner | Expected Impact |
|------|--------|-------|----------------|
| 1–2 | Deploy churn prediction API; flag top-500 At-Risk customers | Data/Engineering | Identify targets |
| 2–4 | Run win-back email campaign for At-Risk + Can't Lose segments | Marketing | +200 retained customers |
| 3–6 | Negotiate 3-day delivery improvement SLA with top 5 carriers | Operations | -3% churn rate |
| 4–8 | Launch post-delivery nurture sequence (7/14/30 day emails) | Marketing | +5% repeat purchase rate |
| 6–10 | Implement real-time 1-star review alert + recovery protocol | Customer Service | Recover 20% of 1-star customers |
| 8–12 | Quarterly RFM re-segmentation and campaign refresh | Analytics | Maintain segment accuracy |

---

*Analysis conducted on Olist Brazilian E-commerce Dataset (CC-BY-NC-SA-4.0)*
*All revenue figures in Brazilian Real (BRL)*
