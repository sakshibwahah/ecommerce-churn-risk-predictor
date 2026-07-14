"""
tab1_executive.py — Executive Dashboard: KPI cards + trend charts.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.data_loader import load_eda_summary, load_churn_predictions, load_clv, load_rfm, get_engine
from utils.charts import DARK_TEMPLATE, FONT


def render():
    st.markdown('## Executive Dashboard')
    st.markdown('*Overview of churn risk, revenue health, and delivery performance.*')

    summary = load_eda_summary()
    churn_df = load_churn_predictions()
    clv_df = load_clv()
    rfm_df = load_rfm()
    engine = get_engine()

    rev_at_risk = 0
    if 'revenue_at_risk' in clv_df.columns:
        rev_at_risk = clv_df['revenue_at_risk'].sum()
    elif 'revenue_at_risk' in churn_df.columns:
        rev_at_risk = churn_df['revenue_at_risk'].sum()

    churn_rate = churn_df['churn'].mean() if 'churn' in churn_df.columns else summary.get('churn_rate', 0.128)

    avg_clv = 0
    if 'CLV' in clv_df.columns:
        avg_clv = clv_df['CLV'].mean()
    elif 'CLV' in churn_df.columns:
        avg_clv = churn_df['CLV'].mean()
    on_time = summary.get('on_time_delivery_rate', 0.92)
    avg_review = summary.get('avg_review_score', 4.0)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric('Revenue at Risk', f'R$ {rev_at_risk:,.0f}',
                delta='High-risk order CLV exposure', delta_color='inverse')
    col2.metric('Churn Risk Rate', f'{churn_rate*100:.1f}%',
                delta='Dissatisfied experience rate',
                delta_color='inverse')
    col3.metric('Avg CLV', f'R$ {avg_clv:,.0f}', delta='Customer lifetime value')
    col4.metric('On-time Delivery', f'{on_time*100:.1f}%',
                delta=f"{(on_time-0.92)*100:+.1f}pp vs 92% target",
                delta_color='normal' if on_time >= 0.92 else 'inverse')
    col5.metric('Avg Review Score', f'{avg_review:.2f}/5.0')

    st.divider()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        try:
            time_df = pd.read_sql("""
                SELECT STRFTIME('%Y-%m', order_purchase_timestamp) AS month,
                       COUNT(*) AS num_orders,
                       ROUND(SUM(payment_value), 2) AS monthly_revenue
                FROM orders o
                JOIN order_payments op ON o.order_id = op.order_id
                WHERE order_status NOT IN ('canceled','unavailable')
                  AND order_purchase_timestamp >= '2017-01-01'
                GROUP BY month ORDER BY month
            """, engine)
            fig_trend = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                     subplot_titles=['Monthly Orders', 'Monthly Revenue (BRL)'],
                                     row_heights=[0.4, 0.6])
            fig_trend.add_trace(go.Scatter(x=time_df['month'], y=time_df['num_orders'],
                                           fill='tozeroy', line_color='#8b5cf6', name='Orders'), row=1, col=1)
            fig_trend.add_trace(go.Scatter(x=time_df['month'], y=time_df['monthly_revenue'],
                                           fill='tozeroy', line_color='#06b6d4', name='Revenue'), row=2, col=1)
            fig_trend.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=380,
                                    showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, width='stretch')
        except Exception as e:
            st.warning(f'Could not load trend data: {e}')

    with col_right:
        if not rfm_df.empty and 'Segment' in rfm_df.columns:
            seg_counts = rfm_df['Segment'].value_counts().reset_index()
            seg_counts.columns = ['Segment', 'Count']
            fig_donut = px.pie(seg_counts, names='Segment', values='Count',
                               hole=0.55, title='Customer Segments',
                               color_discrete_sequence=px.colors.qualitative.Bold)
            fig_donut.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=380,
                                    paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_donut, width='stretch')

    # Revenue at risk bar — can come from churn_predictions directly
    src_df = clv_df if not clv_df.empty else churn_df
    if not src_df.empty and 'customer_state' in src_df.columns and 'revenue_at_risk' in src_df.columns:
        st.markdown('### Revenue at Risk by State (Top 10)')
        state_risk = src_df.groupby('customer_state')['revenue_at_risk'].sum().nlargest(10).reset_index()
        fig_states = px.bar(state_risk, x='customer_state', y='revenue_at_risk',
                            color='revenue_at_risk', color_continuous_scale='Reds',
                            labels={'customer_state': 'State', 'revenue_at_risk': 'Revenue at Risk (BRL)'})
        fig_states.update_layout(template=DARK_TEMPLATE, font_family=FONT,
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_states, width='stretch')
