"""
tab3_churn_predictor.py — Individual order churn risk prediction with SHAP explanation.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.data_loader import load_model, load_churn_predictions
from utils.charts import churn_gauge, DARK_TEMPLATE, FONT

FEATURE_LABELS = {
    'delivery_delay_days':  'Delivery Delay (days)',
    'actual_delivery_days': 'Actual Delivery Time (days)',
    'price':                'Item Price (BRL)',
    'freight_ratio':        'Freight / Price Ratio',
    'product_photos_qty':   'Product Photos Count',
    'description_length':   'Product Description Length',
    'same_state':           'Buyer & Seller Same State',
    'customer_state_enc':   'Customer State (encoded)',
    'category_enc':         'Product Category (encoded)',
    'review_vader_score':   'Review Sentiment (VADER)',
}

RECOMMENDATIONS = {
    'high': (
        'High churn risk. Primary driver is likely delayed or poor delivery. '
        'Proactively contact this customer, offer a partial freight refund, '
        'and flag the seller for performance review.'
    ),
    'medium': (
        'Moderate churn risk. Monitor for a low review score. '
        'Consider a follow-up message asking about delivery satisfaction '
        'before the review window closes.'
    ),
    'low': (
        'Low churn risk. Delivery and order signals look healthy. '
        'Good candidate for an upsell or cross-sell campaign.'
    ),
}


def render():
    st.markdown('## Customer Churn Risk Predictor')
    st.markdown(
        '*Predicts dissatisfied experience (review score 1–2) from fulfillment signals. '
        'All features are observable before the review is submitted — no leakage.*'
    )

    model, iso, scaler, feature_names = load_model()
    churn_df = load_churn_predictions()

    if model is None:
        st.error('Model not found. Run notebook 03_churn_prediction.ipynb.')
        return

    mode = st.radio('Input Mode', ['Lookup by Order ID', 'Manual Feature Input'], horizontal=True)

    if mode == 'Lookup by Order ID':
        if churn_df.empty:
            st.warning('Run the pipeline to generate predictions.')
            return

        id_col = 'order_id' if 'order_id' in churn_df.columns else 'customer_id'

        col_left, col_right = st.columns([2, 1])
        with col_left:
            high_risk = churn_df[churn_df['churn_prob'] > 0.55][id_col].head(150).tolist()
            low_risk  = churn_df[churn_df['churn_prob'] < 0.25][id_col].head(50).tolist()
            sample_ids = (high_risk + low_risk)[:200]
            selected = st.selectbox('Select Order / Customer ID', options=sample_ids)
        with col_right:
            st.caption('Sample includes a mix of high-risk and low-risk orders.')

        if st.button('Predict Risk', type='primary'):
            row = churn_df[churn_df[id_col] == selected]
            if row.empty:
                st.error('ID not found.')
                return
            _show_prediction(row.iloc[0], feature_names, model, iso, scaler,
                             stored_prob=float(row.iloc[0].get('churn_prob', 0)))

    else:
        st.markdown('#### Feature Inputs')
        c1, c2, c3 = st.columns(3)
        with c1:
            delay       = st.slider('Delivery Delay (days past estimate)', -10.0, 30.0, 0.0, 0.5)
            delivery_t  = st.slider('Actual Delivery Time (days)', 1, 60, 12)
            price       = st.slider('Item Price (BRL)', 10.0, 2000.0, 150.0, 5.0)
        with c2:
            photos      = st.slider('Product Photos Count', 1, 20, 3)
            desc_len    = st.slider('Description Length (chars)', 50, 3000, 600, 50)
            same_state  = st.selectbox('Buyer & Seller Same State?', [1, 0],
                                        format_func=lambda x: 'Yes' if x else 'No')
        with c3:
            state_enc   = st.slider('Customer State (0–26)', 0, 26, 13)
            cat_enc     = st.slider('Product Category (0–70)', 0, 70, 10)
            vader_score = st.slider(
                'Review Sentiment (VADER)', -1.0, 1.0, 0.0, 0.05,
                help='Negative values indicate negative sentiment in review text. '
                     '-1 = very negative, 0 = neutral, 1 = positive.'
            )

        inputs = {
            'delivery_delay_days':  delay,
            'actual_delivery_days': delivery_t,
            'price':                price,
            'freight_ratio':        20.0 / max(price, 0.01),
            'product_photos_qty':   photos,
            'description_length':   desc_len,
            'same_state':           same_state,
            'customer_state_enc':   state_enc,
            'category_enc':         cat_enc,
            'review_vader_score':   vader_score,
        }

        if st.button('Predict Risk', type='primary'):
            feat_vec = np.array([inputs.get(f, 0.0) for f in feature_names], dtype=float)
            X_s = scaler.transform(feat_vec.reshape(1, -1))
            raw = float(model.predict_proba(X_s)[0][1])
            prob = float(iso.transform([raw])[0]) if iso is not None else raw
            _show_prediction(pd.Series(inputs), feature_names, model, iso, scaler,
                             stored_prob=prob)


def _show_prediction(row, feature_names, model, iso, scaler, stored_prob: float):
    import shap

    feat_vals = np.array(
        [float(row.get(f, 0) or 0) for f in feature_names], dtype=float
    )
    X_s = scaler.transform(feat_vals.reshape(1, -1))

    prob = stored_prob
    risk = 'high' if prob > 0.55 else 'medium' if prob > 0.30 else 'low'

    st.divider()
    col_gauge, col_info = st.columns([1, 1])

    with col_gauge:
        st.plotly_chart(churn_gauge(prob), width='stretch')

    with col_info:
        risk_label = {'high': 'High Risk', 'medium': 'Medium Risk', 'low': 'Low Risk'}[risk]
        st.markdown(f'### {risk_label}')
        st.markdown(f'**Churn Risk Probability:** {prob*100:.1f}%')
        st.info(RECOMMENDATIONS[risk])

        # Key signals
        delay = float(row.get('delivery_delay_days', 0) or 0)
        score = float(row.get('review_score', 0) or 0)
        if delay > 7:
            st.warning(f'Delivery was {delay:.0f} days late — primary risk driver.')
        if score and score <= 2:
            st.error(f'Review score: {score:.0f}/5 — confirmed dissatisfied.')
        elif score and score >= 4:
            st.success(f'Review score: {score:.0f}/5 — satisfied customer.')

    st.markdown('#### Feature Impact (SHAP)')
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_s)
        sv_arr = np.array(sv).flatten()[:len(feature_names)]

        shap_df = pd.DataFrame({
            'Feature':    [FEATURE_LABELS.get(f, f) for f in feature_names],
            'SHAP Value': sv_arr,
            'Feature Value': feat_vals,
        }).sort_values('SHAP Value', key=abs, ascending=True)

        colors = ['#ef4444' if v > 0 else '#10b981' for v in shap_df['SHAP Value']]
        fig = go.Figure(go.Bar(
            x=shap_df['SHAP Value'],
            y=shap_df['Feature'],
            orientation='h',
            marker_color=colors,
            text=[f'{v:+.3f}' for v in shap_df['SHAP Value']],
            textposition='outside',
        ))
        fig.update_layout(
            title='SHAP Waterfall — Feature Contributions to Risk Score',
            xaxis_title='SHAP Value',
            template=DARK_TEMPLATE,
            font_family=FONT,
            height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, width='stretch')
        st.caption('Red bars increase churn risk. Green bars reduce it.')
    except Exception as e:
        st.warning(f'SHAP explanation unavailable: {e}')
