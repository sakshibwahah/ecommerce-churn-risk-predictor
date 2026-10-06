import sqlite3, warnings, json, textwrap
import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')

# ── Load data ─────────────────────────────────────────────────────────────────
con = sqlite3.connect('data/olist.db')
query = '''
WITH item_agg AS (
    SELECT
        oi.order_id,
        SUM(oi.price)                       AS price,
        SUM(oi.freight_value)               AS freight_value,
        MAX(p.product_photos_qty)           AS product_photos_qty,
        MAX(p.product_description_lenght)   AS description_length,
        MAX(s.seller_state)                 AS seller_state,
        MAX(p.product_category_name)        AS product_category_name
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    JOIN sellers  s ON oi.seller_id  = s.seller_id
    GROUP BY oi.order_id
)
SELECT
    o.order_id,
    c.customer_unique_id,
    r.review_score,
    r.review_comment_message,
    julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date) as delivery_delay_days,
    julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp) as actual_delivery_days,
    ia.price,
    ia.freight_value,
    ia.product_photos_qty,
    ia.description_length,
    c.customer_state,
    ia.seller_state,
    ia.product_category_name
FROM orders o
JOIN order_reviews r  ON o.order_id    = r.order_id
JOIN item_agg ia      ON o.order_id    = ia.order_id
JOIN customers c      ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
'''
df_raw = pd.read_sql_query(query, con)
con.close()
df_raw = df_raw.drop_duplicates(subset='order_id', keep='first').reset_index(drop=True)
print(f"Rows loaded: {len(df_raw)}")

# ── Feature engineering ───────────────────────────────────────────────────────
df = df_raw.copy()
df['freight_ratio'] = df['freight_value'] / df['price']
df['same_state'] = (df['customer_state'] == df['seller_state']).astype(int)

analyzer = SentimentIntensityAnalyzer()
pt_lexicon = {
    'atraso': -2.5, 'defeito': -3.0, 'cancelar': -2.5, 'péssimo': -3.5,
    'ruim': -2.5, 'lixo': -3.0, 'falso': -3.0, 'quebrado': -2.5,
    'demora': -2.0, 'nunca': -1.5, 'não': -1.0,
    'ótimo': 2.5, 'bom': 2.0, 'excelente': 3.0, 'perfeito': 3.0
}
analyzer.lexicon.update(pt_lexicon)

def get_vader_score(text):
    if pd.isna(text) or str(text).strip() == '':
        return 0.0
    return analyzer.polarity_scores(str(text))['compound']

df['review_vader_score'] = df['review_comment_message'].apply(get_vader_score)

le_state = LabelEncoder()
df['customer_state_enc'] = le_state.fit_transform(df['customer_state'].astype(str))
le_category = LabelEncoder()
df['category_enc'] = le_category.fit_transform(df['product_category_name'].astype(str))

df['churn_risk'] = (df['review_score'] <= 2).astype(int)

# ── Feature sets ──────────────────────────────────────────────────────────────
FEATURES_WITH = [
    'delivery_delay_days', 'actual_delivery_days', 'price', 'freight_ratio',
    'product_photos_qty', 'description_length', 'same_state',
    'customer_state_enc', 'category_enc', 'review_vader_score'
]

FEATURES_WITHOUT = [
    'delivery_delay_days', 'actual_delivery_days', 'price', 'freight_ratio',
    'product_photos_qty', 'description_length', 'same_state',
    'customer_state_enc', 'category_enc'
]

df_clean = df[FEATURES_WITH + ['churn_risk']].dropna()
y = df_clean['churn_risk'].values
print(f"Clean rows: {len(df_clean)}")
print(f"Churn rate: {y.mean():.3f}  |  Negative: {(y==0).sum()}  Positive: {(y==1).sum()}")

# ── Model params (identical to notebook 03) ───────────────────────────────────
n0, n1 = (y == 0).sum(), (y == 1).sum()
clf_params = {
    'n_estimators': 400, 'max_depth': 4, 'learning_rate': 0.05,
    'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 10,
    'scale_pos_weight': round(n0 / n1),
    'eval_metric': 'auc', 'objective': 'binary:logistic',
    'random_state': 42, 'n_jobs': -1
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ── Run 1: WITH review_vader_score ────────────────────────────────────────────
X_with = StandardScaler().fit_transform(df_clean[FEATURES_WITH].astype(float))
scores_with = []
for tr, val in cv.split(X_with, y):
    m = XGBClassifier(**clf_params)
    m.fit(X_with[tr], y[tr])
    scores_with.append(roc_auc_score(y[val], m.predict_proba(X_with[val])[:, 1]))

auc_with = np.mean(scores_with)
std_with  = np.std(scores_with)
print(f"\nWITH  review_vader_score  →  CV AUC: {auc_with:.4f} ± {std_with:.4f}")

# ── Run 2: WITHOUT review_vader_score ─────────────────────────────────────────
X_without = StandardScaler().fit_transform(df_clean[FEATURES_WITHOUT].astype(float))
scores_without = []
for tr, val in cv.split(X_without, y):
    m = XGBClassifier(**clf_params)
    m.fit(X_without[tr], y[tr])
    scores_without.append(roc_auc_score(y[val], m.predict_proba(X_without[val])[:, 1]))

auc_without = np.mean(scores_without)
std_without  = np.std(scores_without)
print(f"WITHOUT review_vader_score →  CV AUC: {auc_without:.4f} ± {std_without:.4f}")

drop = auc_with - auc_without
print(f"\nAUC drop from removing sentiment: {drop:.4f}")
print(f"Sentiment accounts for {drop / auc_with * 100:.1f}% of the total AUC")
