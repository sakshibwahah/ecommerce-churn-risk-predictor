"""
charts.py — Reusable Plotly chart functions for the Streamlit dashboard.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

DARK_TEMPLATE = 'plotly_dark'
FONT = 'Inter'

PALETTE = {
    'primary':   '#8b5cf6',
    'secondary': '#06b6d4',
    'danger':    '#ef4444',
    'success':   '#10b981',
    'warning':   '#f59e0b',
}


def rfm_3d_scatter(rfm_df: pd.DataFrame, sample_n: int = 5000) -> go.Figure:
    df = rfm_df.sample(min(sample_n, len(rfm_df)), random_state=42) if len(rfm_df) > sample_n else rfm_df
    hover = ['customer_id', 'RFM_Score'] if 'RFM_Score' in df.columns else None
    fig = px.scatter_3d(
        df, x='recency', y='frequency', z='monetary',
        color='Segment', opacity=0.75,
        title='3D RFM Customer Segmentation',
        labels={'recency': 'Recency (days)', 'frequency': 'Frequency', 'monetary': 'Monetary (BRL)'},
        color_discrete_sequence=px.colors.qualitative.Bold,
        hover_data=hover,
    )
    fig.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=550,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig


def segment_donut(rfm_df: pd.DataFrame) -> go.Figure:
    counts = rfm_df['Segment'].value_counts().reset_index()
    counts.columns = ['Segment', 'Count']
    fig = px.pie(counts, names='Segment', values='Count',
                 hole=0.55, color_discrete_sequence=px.colors.qualitative.Bold,
                 title='Customer Segment Distribution')
    fig.update_layout(template=DARK_TEMPLATE, font_family=FONT,
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig


def churn_gauge(prob: float) -> go.Figure:
    color = PALETTE['success'] if prob < 0.3 else PALETTE['warning'] if prob < 0.55 else PALETTE['danger']
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=prob * 100,
        title={'text': 'Churn Risk (%)', 'font': {'size': 18, 'color': 'white'}},
        number={'suffix': '%', 'font': {'size': 36, 'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'white'},
            'bar':  {'color': color},
            'bgcolor': '#1a1a2e',
            'steps': [
                {'range': [0, 30],  'color': '#064e3b'},
                {'range': [30, 55], 'color': '#78350f'},
                {'range': [55, 100],'color': '#7f1d1d'},
            ],
            'threshold': {'line': {'color': 'white', 'width': 2}, 'thickness': 0.75, 'value': prob * 100},
        }
    ))
    fig.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=280,
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig


def simulator_bar(before_n: int, after_n: int,
                  before_rev: float, after_rev: float) -> go.Figure:
    fig = make_subplots(rows=1, cols=2,
                         subplot_titles=['At-Risk Orders', 'Revenue at Risk (BRL)'])
    colors = [PALETTE['danger'], PALETTE['success']]
    fig.add_trace(go.Bar(x=['Baseline', 'Post-Intervention'], y=[before_n, after_n],
                          marker_color=colors, showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=['Baseline', 'Post-Intervention'], y=[before_rev, after_rev],
                          marker_color=colors, showlegend=False), row=1, col=2)
    fig.update_layout(template=DARK_TEMPLATE, font_family=FONT, height=320,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig
