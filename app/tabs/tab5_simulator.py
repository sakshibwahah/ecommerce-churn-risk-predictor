"""
tab5_simulator.py — Intervention Simulator.

Models the customer-level impact of two operational levers:
  1. Reducing delivery delay
  2. Improving review scores (proxy for quality improvements)

Re-scores each customer's churn probability with adjusted features,
then computes how many customers are retained and how much revenue is saved.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_loader import load_churn_predictions, load_model
from utils.charts import DARK_TEMPLATE, FONT


def _rescore(df: pd.DataFrame, model, iso, scaler, feature_names: list,
             delay_delta: float, freight_delta: float) -> np.ndarray:
    """
    Apply intervention deltas to delivery and freight features, then re-score
    each order's churn risk using the trained model.
    """
    X = df[feature_names].copy().astype(float)

    if 'delivery_delay_days' in X.columns:
        X['delivery_delay_days'] = (X['delivery_delay_days'] - delay_delta).clip(lower=-20)
    if 'actual_delivery_days' in X.columns:
        X['actual_delivery_days'] = (X['actual_delivery_days'] - delay_delta * 0.5).clip(lower=1)
    if 'freight_value' in X.columns and freight_delta > 0:
        reduction = freight_delta / 100.0
        X['freight_value']  = (X['freight_value'] * (1 - reduction)).clip(lower=0)
    if 'freight_ratio' in X.columns and freight_delta > 0:
        reduction = freight_delta / 100.0
        X['freight_ratio']  = (X['freight_ratio'] * (1 - reduction)).clip(lower=0, upper=5)

    X_scaled = scaler.transform(X.values)
    raw_probs = model.predict_proba(X_scaled)[:, 1]
    if iso is not None:
        return iso.transform(raw_probs)
    return raw_probs


def render():
    st.markdown('## Intervention Simulator')
    st.markdown(
        '*Model the revenue impact of operational improvements. '
        'Each customer is individually re-scored with adjusted features.*'
    )

    churn_df = load_churn_predictions()
    model, iso, scaler, feature_names = load_model()

    if churn_df.empty:
        st.error('Churn predictions not found. Run the pipeline first.')
        return
    if model is None:
        st.error('Model not found. Run notebook 03_churn_prediction.ipynb.')
        return

    delay_available   = 'delivery_delay_days' in feature_names
    freight_available = 'freight_ratio' in feature_names or 'freight_value' in feature_names

    st.markdown('### Intervention Parameters')
    col1, col2, col3 = st.columns(3)

    with col1:
        delay_reduction = st.slider(
            'Reduce delivery delay by (days)', 0.0, 10.0, 2.0, 0.5,
            disabled=not delay_available,
            help='Number of days by which avg delivery delay is improved'
        )
    with col2:
        freight_reduction = st.slider(
            'Reduce freight cost by (%)', 0, 50, 10, 5,
            disabled=not freight_available,
            help='Percentage reduction in freight value (e.g. subsidise shipping for at-risk orders)'
        )
    with col3:
        intervention_cost_per_customer = st.number_input(
            'Intervention cost per order (BRL)', min_value=0, max_value=500,
            value=25, step=5,
            help='Estimated cost of outreach/discount per at-risk order targeted'
        )

    if not (delay_available or freight_available):
        st.warning(
            'Model features do not include delivery delay or freight. '
            'Retrain the model to enable simulation.'
        )
        return

    run = st.button('Run Simulation', type='primary')
    if not run:
        return

    with st.spinner('Re-scoring all customers...'):
        df = churn_df.copy()

        # Ensure all feature columns exist and are numeric
        for feat in feature_names:
            if feat not in df.columns:
                df[feat] = 0.0
            df[feat] = pd.to_numeric(df[feat], errors='coerce').fillna(0.0)

        baseline_probs = df['churn_prob'].values.copy()
        new_probs = _rescore(df, model, iso, scaler, feature_names,
                             delay_reduction, float(freight_reduction))

        df['new_churn_prob'] = new_probs
        df['baseline_churn_prob'] = baseline_probs

        # Customers who flip from high-risk (>0.5) to lower-risk (<=0.5)
        threshold = 0.5
        baseline_churned = baseline_probs > threshold
        new_churned = new_probs > threshold
        rescued = baseline_churned & ~new_churned

        n_baseline = int(baseline_churned.sum())
        n_new = int(new_churned.sum())
        n_rescued = int(rescued.sum())

        # Revenue impact — use payment_value to match the executive dashboard's
        # revenue_at_risk = payment_value × churn_prob definition exactly.
        pay_col = 'payment_value' if 'payment_value' in df.columns else 'total_spend'
        if pay_col in df.columns:
            baseline_rev_risk = float((df[pay_col] * df['baseline_churn_prob']).sum())
            new_rev_risk      = float((df[pay_col] * df['new_churn_prob']).sum())
        elif 'revenue_at_risk' in df.columns:
            # Fall back to the precomputed column if payment_value is unavailable
            baseline_rev_risk = float(df['revenue_at_risk'].sum())
            new_rev_risk      = baseline_rev_risk * (n_new / max(n_baseline, 1))
        else:
            baseline_rev_risk, new_rev_risk = 0.0, 0.0


        revenue_saved = max(0.0, baseline_rev_risk - new_rev_risk)
        total_cost = n_rescued * intervention_cost_per_customer
        net_gain = revenue_saved - total_cost
        roi = (net_gain / total_cost * 100) if total_cost > 0 else 0.0

    st.divider()
    st.markdown('### Results')

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Orders Retained', f'{n_rescued:,}',
              delta=f'-{n_rescued} from at-risk list')
    m2.metric('Revenue Saved (BRL)', f'R$ {revenue_saved:,.0f}',
              delta='Matches dashboard Revenue at Risk definition')
    m3.metric('Net Gain after Costs (BRL)', f'R$ {net_gain:,.0f}',
              delta_color='normal' if net_gain >= 0 else 'inverse',
              delta=f'ROI: {roi:+.0f}%')
    m4.metric('New At-Risk Rate',
              f"{n_new / len(df) * 100:.1f}%",
              delta=f"{(n_new - n_baseline) / len(df) * 100:+.1f}pp",
              delta_color='normal' if n_new <= n_baseline else 'inverse')


    # Probability shift distribution
    prob_shift = new_probs - baseline_probs
    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=prob_shift, nbinsx=60,
        marker_color='#8b5cf6', opacity=0.8,
        name='Prob shift'
    ))
    fig_dist.add_vline(x=0, line_color='white', line_dash='dash', line_width=1)
    fig_dist.update_layout(
        title='Distribution of Churn Probability Change per Customer',
        xaxis_title='Change in Churn Probability',
        yaxis_title='Number of Customers',
        template=DARK_TEMPLATE, font_family=FONT, height=300,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_dist, width='stretch')

    # Before / after comparison chart
    fig_compare = make_subplots(rows=1, cols=2,
                                 subplot_titles=['At-Risk Customers', 'Revenue at Risk (BRL)'])
    bar_color = ['#ef4444', '#10b981']
    fig_compare.add_trace(go.Bar(x=['Baseline', 'After Intervention'], y=[n_baseline, n_new],
                                  marker_color=bar_color, showlegend=False), row=1, col=1)
    fig_compare.add_trace(go.Bar(x=['Baseline', 'After Intervention'],
                                  y=[baseline_rev_risk, new_rev_risk],
                                  marker_color=bar_color, showlegend=False), row=1, col=2)
    fig_compare.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=300,
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_compare, width='stretch')

    # Savings breakdown table — all numeric, no formatted strings (avoids Arrow errors)
    st.markdown('#### Summary Table')
    breakdown = pd.DataFrame({
        'Metric': ['At-Risk Orders', 'Revenue at Risk (BRL)', 'At-Risk Rate (%)',
                   'Intervention Cost (BRL)', 'Net Revenue Gain (BRL)', 'ROI (%)'],
        'Baseline': [n_baseline, round(baseline_rev_risk, 0),
                     round(n_baseline / len(df) * 100, 2), 0, 0, 0],
        'Post-Intervention': [n_new, round(new_rev_risk, 0),
                              round(n_new / len(df) * 100, 2),
                              round(total_cost, 0), round(net_gain, 0), round(roi, 1)],
    })
    st.dataframe(breakdown, hide_index=True, width='stretch')

    if n_rescued > 0:
        st.markdown('#### Top Rescued Orders (Highest Revenue at Risk)')
        rescued_df = df[rescued].copy()
        rescued_df['prob_reduction'] = (rescued_df['baseline_churn_prob']
                                        - rescued_df['new_churn_prob']).round(3)
        sort_col = pay_col if pay_col in rescued_df.columns else 'prob_reduction'
        show_cols = [c for c in ['order_id', 'customer_id', 'customer_state', pay_col,
                                  'revenue_at_risk', 'baseline_churn_prob',
                                  'new_churn_prob', 'prob_reduction']
                     if c in rescued_df.columns]
        st.dataframe(
            rescued_df[show_cols].sort_values(sort_col, ascending=False).head(20),
            hide_index=True, width='stretch'
        )
