"""
tab2_segments.py — Customer Segments: RFM 3D scatter + segment profiling.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_rfm, load_churn_predictions
from utils.charts import rfm_3d_scatter, segment_donut, DARK_TEMPLATE, FONT


def render():
    st.markdown('## Customer Segments')
    st.markdown('*RFM-based segmentation of 100k+ customers into actionable groups.*')

    rfm_df = load_rfm()
    churn_df = load_churn_predictions()

    if rfm_df.empty:
        st.error('RFM data not found. Please run Notebook 02 first.')
        return

    if not churn_df.empty and 'churn_prob' in churn_df.columns:
        rfm_df = rfm_df.merge(
            churn_df[['customer_unique_id', 'churn_prob']].drop_duplicates('customer_unique_id'),
            on='customer_unique_id', how='left'
        )

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        selected_segments = st.multiselect(
            'Filter Segments',
            options=sorted(rfm_df['Segment'].dropna().unique().tolist()),
            default=sorted(rfm_df['Segment'].dropna().unique().tolist())
        )
    with col_ctrl2:
        sample_size = st.slider('3D Plot Sample Size', 500, 10000, 3000, 500)

    filtered = rfm_df[rfm_df['Segment'].isin(selected_segments)]

    st.plotly_chart(rfm_3d_scatter(filtered, sample_n=sample_size), width='stretch')

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.plotly_chart(segment_donut(filtered), width='stretch')

    with col_right:
        st.markdown('#### Segment Profile')
        # Show RFM scores (1–5) rather than raw frequency count.
        # Olist is a single-purchase marketplace: 97% of customers have exactly
        # 1 order, so raw frequency is uninformative. The F score (rank-based
        # quintile) captures relative purchase frequency correctly.
        profile_agg = {
            'Customers':     ('customer_id', 'count'),
            'Avg_Recency':   ('recency',     'mean'),
            'Avg_R_Score':   ('R',           'mean'),
            'Avg_F_Score':   ('F',           'mean'),
            'Avg_M_Score':   ('M',           'mean'),
            'Avg_Monetary':  ('monetary',    'mean'),
            'Total_Revenue': ('monetary',    'sum'),
        }
        profile = filtered.groupby('Segment').agg(**profile_agg).round(2)
        profile = profile.sort_values('Total_Revenue', ascending=False)
        if 'churn_prob' in filtered.columns:
            profile['Avg_Churn_Prob'] = filtered.groupby('Segment')['churn_prob'].mean().round(3)
        st.dataframe(profile, width='stretch')
        st.caption(
            'R/F/M scores are quintile ranks (1=worst, 5=best). '
            'Raw frequency is 1 for most customers — Olist anonymises each transaction with a unique customer_id.'
        )


    st.download_button(
        'Download Segment Data (CSV)',
        filtered.to_csv(index=False),
        file_name='rfm_segments_filtered.csv',
        mime='text/csv'
    )
